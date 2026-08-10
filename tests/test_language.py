"""Language comprehension — the text→meaning bridge, run on the rewrite engine.

Stage 1 (this file): the lexical layer — characters (the receptors) are reduced
to Word/Number constituents by recognition rules, longest-match and boundary-
aware, with multi-digit numbers folded left-to-right. All on the engine.
"""
from __future__ import annotations

from domains import language as lang

_FORMS = [("what", "WH"), ("is", "COP"), ("the", "DET"), ("next", "ADJ"),
          ("term", "N"), ("of", "PREP"), ("index", "N"), ("in", "PREP"),
          ("determinant", "N")]


def test_lexical_access_words_and_numbers():
    out = lang.lex("what is the next term of 1, 1, 2, 3, 5, 8", _FORMS)
    kinds = [(c["kind"], c.get("form", c.get("value"))) for c in out]
    assert kinds == [("Word", "what"), ("Word", "is"), ("Word", "the"),
                     ("Word", "next"), ("Word", "term"), ("Word", "of"),
                     ("Number", 1), ("Number", 1), ("Number", 2),
                     ("Number", 3), ("Number", 5), ("Number", 8)]


def test_longest_match_and_multidigit():
    # 'index' wins over its prefix 'in'; '124' folds from three digit chars
    out = lang.lex("index 124", _FORMS)
    assert out == [{"kind": "Word", "form": "index", "cat": "N"},
                   {"kind": "Number", "value": 124}]


def test_categories_carried():
    out = lang.lex("the determinant of 12", _FORMS)
    assert [c.get("cat") for c in out if c["kind"] == "Word"] == ["DET", "N", "PREP"]
    assert out[-1] == {"kind": "Number", "value": 12}


# --- Stage 2: general argument-structure composition (Merge) ----------------

_LEX = [
    {"form": "determinant", "concept": "det", "args": [{"role": "of", "marker": "of", "dir": "R"}]},
    {"form": "trace", "concept": "trace", "args": [{"role": "of", "marker": "of", "dir": "R"}]},
    {"form": "product", "concept": "product",
     "args": [{"role": "a", "marker": "of", "dir": "R"}, {"role": "b", "marker": "and", "dir": "R"}]},
    {"form": "plus", "concept": "plus",
     "args": [{"role": "left", "dir": "L"}, {"role": "right", "dir": "R"}]},
    {"form": "A", "concept": "A"}, {"form": "B", "concept": "B"}, {"form": "M", "concept": "M"},
    {"form": "of", "mark": True}, {"form": "and", "mark": True},
    {"form": "the", "drop": True}, {"form": "is", "drop": True}, {"form": "what", "drop": True},
]


def test_composition_marked_and_infix():
    assert lang.comprehend("determinant of M", _LEX) == [{"force": "tell", "det": {"of": "M"}}]
    assert lang.comprehend("A plus B", _LEX) == [
        {"force": "tell", "plus": {"left": "A", "right": "B"}}]


def test_composition_recursive_nesting():
    # the product closes (saturates) before trace binds it — bottom-up Merge
    assert lang.comprehend("trace of the product of A and B", _LEX) == [
        {"force": "tell", "trace": {"of": {"product": {"a": "A", "b": "B"}}}}]


def test_prosody_force_from_punctuation():
    assert lang.comprehend("what is the determinant of M?", _LEX)[0]["force"] == "ask"
    assert lang.comprehend("determinant of M", _LEX)[0]["force"] == "tell"


def test_grammar_is_vocabulary_independent():
    # add a brand-new sign at runtime; the SAME rules compose it, no new grammar
    lex = _LEX + [{"form": "inverse", "concept": "inverse",
                   "args": [{"role": "of", "marker": "of", "dir": "R"}]}]
    assert lang.comprehend("inverse of the product of A and B", lex) == [
        {"force": "tell", "inverse": {"of": {"product": {"a": "A", "b": "B"}}}}]


# --- production: comprehension's inverse over the same signs -----------------

def test_production_explicit():
    det = {"force": "tell", "det": {"of": "M"}}
    assert lang.produce(det, _LEX) == "determinant of M"
    plus = {"force": "tell", "plus": {"left": "A", "right": "B"}}
    assert lang.produce(plus, _LEX) == "A plus B"


def test_production_emits_force_prosody():
    assert lang.produce({"force": "ask", "det": {"of": "M"}}, _LEX).endswith("?")


def test_comprehend_produce_round_trip():
    # the real correctness criterion: produce∘comprehend recovers the meaning,
    # for leaf, infix, marked, deeply-nested, and interrogative utterances
    for text in ["determinant of M", "A plus B",
                 "trace of the product of A and B",
                 "what is the determinant of M?"]:
        m = lang.comprehend(text, _LEX)[0]
        assert lang.comprehend(lang.produce(m, _LEX), _LEX)[0] == m


# --- the expanded core lexicon scales the faculty's range (same grammar) ----

def test_core_lexicon_breadth():
    lex = lang.core_lexicon()
    assert lang.comprehend("the index of H in G", lex) == [
        {"force": "tell", "index": {"a": "H", "b": "G"}}]
    assert lang.comprehend("M is invertible", lex) == [
        {"force": "tell", "invertible": {"arg": "M"}}]
    assert lang.comprehend("is G normal?", lex) == [
        {"force": "ask", "normal": {"arg": "G"}}]
    assert lang.comprehend("the inverse of the product of A and B", lex) == [
        {"force": "tell", "inverse": {"of": {"product": {"a": "A", "b": "B"}}}}]


def test_core_lexicon_round_trips():
    lex = lang.core_lexicon()
    for text in ["what is the determinant of M?", "the index of H in G",
                 "M is invertible", "the order of G", "A equals B",
                 "the inverse of the product of A and B"]:
        m = lang.comprehend(text, lex)[0]
        assert lang.comprehend(lang.produce(m, lex), lex)[0] == m


def test_core_lexicon_hle_domain():
    # HLE-domain vocabulary: group theory, multi-word technical terms, counts,
    # predicates, and the inference capabilities — all on the same grammar
    lex = lang.core_lexicon()
    assert lang.comprehend("how many subgroups of G", lex) == [
        {"force": "tell", "count": {"of": {"subgroups": {"of": "G"}}}}]
    assert lang.comprehend("the Euler characteristic of X", lex) == [
        {"force": "tell", "euler": {"of": "X"}}]
    assert lang.comprehend("is G abelian?", lex) == [
        {"force": "ask", "abelian": {"arg": "G"}}]
    assert lang.comprehend("the Wolfram code of the automaton", lex) == [
        {"force": "tell", "wolfram_code": {"of": "automaton"}}]
    # broad round-trip over the HLE-domain phrasings
    for text in ["the kernel of f", "the gcd of A and B", "is f injective?",
                 "the next term of the sequence", "how many generators of G",
                 "the index of H in G", "the rank of the matrix"]:
        m = lang.comprehend(text, lex)[0]
        assert lang.comprehend(lang.produce(m, lex), lex)[0] == m

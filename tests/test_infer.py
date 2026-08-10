"""Inverse inference — discovering a generating rule from observed data.

Two modes, both with the rule living in the graph as Term-trees:
  * DIRECT EXTRACTION — an elementary CA's Wolfram code is read off its
    transitions (the data fixes the rule; ``ca_infer``);
  * HYPOTHESIS SEARCH — a sequence's recurrence is found by testing candidate
    rule-Terms against the data (``sequence_infer``).
Both reproduce real HLE math answers (CA = 73 for i=234; the Hofstadter
recurrence for i=312).
"""
from __future__ import annotations

from domains import ca_infer as ci
from domains import sequence_infer as si


def _evolve(row, code, steps):
    grid = [row]
    for _ in range(steps):
        r = grid[-1]
        W = len(r)
        grid.append([(code >> (4 * r[(x - 1) % W] + 2 * r[x] + 1 * r[(x + 1) % W])) & 1
                     for x in range(W)])
    return grid


def test_ca_wolfram_code_round_trip():
    # generate evolutions from known rules, then INFER the rule back. A wide
    # varied row + enough steps exercises all 8 neighbourhoods, so the code is
    # fully determined (as it is for HLE i=234, whose rule is 73).
    import random
    random.seed(0)
    row = [random.randint(0, 1) for _ in range(80)]
    for code in (73, 110, 30, 90, 150, 54):
        assert ci.infer_wolfram_code(_evolve(row, code, 40)) == code


def test_ca_inference_is_graph_resident():
    # the inference is a single Term evaluated over the loaded world
    grid = _evolve([int(c) for c in "01101001100101101001"], 110, 12)
    from substrate import TypedGraph
    g = TypedGraph()
    anchors = ci.load_evolution(g, grid)
    code = ci.wolfram_code_term().evaluate(
        {"body": anchors["body"], "idx": anchors["idx"],
         "_resolve_concept": lambda n: None}, g)
    assert code == 110


def test_recurrence_inference():
    S1 = [1, 0] * 9
    S2 = list(range(1, 21))
    S3 = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
    S4 = [1, 1, 2, 2, 2, 4, 3, 4, 4, 4, 8, 5, 5, 8, 8, 6, 8, 12, 8, 11, 9, 9, 10,
          13, 16, 9, 12, 20, 10, 12, 23, 12, 15, 21, 13, 17, 18, 19, 19, 22, 21, 19]
    assert si.infer_recurrence(S1) == "s[n] = -s[n-1] + 1"
    assert si.infer_recurrence(S2) == "s[n] = s[n-1] + 1"
    assert si.infer_recurrence(S3) == "s[n] = s[n-1] + s[n-2]"
    # HLE i=312: a self-referential (Hofstadter) recurrence, found by search
    assert si.infer_recurrence(S4) == "s[n] = s[n - s[n-1] - 1] + s[n - s[n-2] - 1]"


def test_recurrence_inference_reports_no_fit():
    # a sequence outside the hypothesis space yields no rule (honest miss)
    assert si.infer_recurrence([2, 3, 5, 7, 11, 13, 17, 19, 23]) is None

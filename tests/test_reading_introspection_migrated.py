"""test_reading_introspection_migrated — the agent READS ITS OWN READING TRAIL.

Phase-1 introspection slice: `reflect("reading_trace", ...)` (routed by the
universal `drive()`) reads the reading collapse trail off the graph — the held
construction codebook (with any construction it MINTED), the sd-loop observations
it stamped, and the predications it grounded — the SAME way `_run_self_shape`
reads the seven meta-shapes. Pure graph read: no Python decides, and it never
perturbs the parse core (additive faculty).

No LLM, no network. Reads real Grimm/encyclopedic prose via reading_collapse.
"""
from __future__ import annotations

import ast
import inspect

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc
from domains import reflective_faculty as rf


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _warm():
    dl.warm_wordnet("en")


def test_reading_trace_is_registered_faculty():
    assert "reading_trace" in rf._DISPATCH
    assert rf._DISPATCH["reading_trace"] is rf._run_reading_trace


def test_reading_trace_reads_codebook_after_ensure():
    """After the codebook is installed, the trace reads the held construction
    codebook off the graph (definitional / event / enumeration / ... present)."""
    ag = _fresh()
    rc.ensure_codebook(ag)
    tr = rf.reflect("reading_trace", None, ag.s)
    assert tr.get("reading_trace")
    assert tr["codebook_size"] >= 8
    assert "definitional" in tr["constructions"]
    assert "event" in tr["constructions"]


def test_reading_trace_surfaces_reading_concepts():
    """Reading real prose writes reading Concepts; the trace reads them back off
    the graph (the reading Concept pool with source=='reading_collapse')."""
    _warm()
    ag = _fresh()
    rc.read_clause(ag, "a dog is an animal", write=True, learn=False)
    tr = rf.reflect("reading_trace", None, ag.s)
    assert "dog" in tr["concepts"]
    assert "animal" in tr["concepts"]


def test_reading_trace_surfaces_grounded_predications():
    """When the reading predication edge is admissible (a grounding-seeded agent —
    here simulated by the same durable-trace write reading_collapse uses when Γ
    admits it), the trace reads the predication back off the graph as [rel, a, b]."""
    ag = _fresh()
    rc.ensure_codebook(ag)
    a = ag.s.add_node("Concept", {"name": "dog", "surface": "dog", "source": "reading_collapse"})
    b = ag.s.add_node("Concept", {"name": "animal", "surface": "animal", "source": "reading_collapse"})
    ag.s._inner.add_edge_unchecked(a, "is_a", b, {"construction": "definitional",
                                                  "source": "reading_collapse"})
    tr = rf.reflect("reading_trace", None, ag.s)
    assert ["is_a", "dog", "animal"] in tr["predications"]
    assert tr["n_predications"] >= 1


def test_reading_trace_surfaces_minted_constructions():
    """A MINTED construction (installed by the sd-loop-driven learn path) is a
    ShapeSignature learned==1.0; the trace surfaces it in `minted_constructions`."""
    ag = _fresh()
    rc.ensure_codebook(ag)
    inst = rc._install_construction(ag, [["POSSESS"], ["OF"]], ["x", "y"])
    tr = rf.reflect("reading_trace", None, ag.s)
    assert tr["n_minted"] >= 1
    assert inst["name"] in tr["minted_constructions"]


def test_reading_trace_honest_null_on_fresh_agent():
    """A fresh agent that has read nothing (no codebook, no trail) gets an honest
    unwired answer, never a fabricated trace."""
    ag = _fresh()
    tr = rf.reflect("reading_trace", None, ag.s)
    assert "unwired" in tr


def test_reading_trace_meta_arg_focuses_predications():
    _warm()
    ag = _fresh()
    rc.read_clause(ag, "a dog is an animal", write=True, learn=False)
    tr = rf.reflect("reading_trace", "dog", ag.s)
    assert "dog" in tr["concepts"]
    assert "animal" not in tr["concepts"]      # focus filters to names containing 'dog'


def test_reading_trace_is_pure_read_no_decision():
    """SOURCE AUDIT: the faculty is a graph read — no max()/min()/sorted-decides,
    no add_node/add_edge/set_attr (it never mutates), mirroring _run_self_shape."""
    src = inspect.getsource(rf._run_reading_trace)
    for banned in ("add_node", "add_edge", "set_attr", "remove_node", "run_rules"):
        assert banned not in src, f"introspection faculty must not mutate ({banned})"
    tree = ast.parse(src.lstrip())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("max", "min"), "a Python max()/min() decides"

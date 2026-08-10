"""The agent decomposes a written compound by SHAPE — recognising known morphemes,
the reading chosen by its own COMPRESSION selector (minimum description length),
the decision a graph-resident Argmin Term. Grounded in the morpheme science the
agent read (smallest meaningful unit; morphological decomposition / word
recognition), NOT an orthographic camelCase rule.

This is the "based on shape — how a human parses it" decomposition
(domains/morpheme_decomposition.py), mirroring forward_segmentation's
architecture: Python computes the morpheme code statistic from the agent's own
corpus; the DECISION (which segmentation) is the seeded Argmin over candidate
readings by their description-length bits.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains import morpheme_decomposition as md


def _ctx():
    code, held = md.corpus_morpheme_code()
    wa = WorldAdapter()
    md.agent_decide_decomposition_mechanism(wa.s)
    return wa, code, held


# ---------------------------------------------------------------------------
# decomposition is by SHAPE (held-morpheme recognition), not orthographic cues
# ---------------------------------------------------------------------------

def test_unmarked_compounds_split_at_morpheme_boundaries():
    """No camelCase / separator — the agent recognises the morphemes by shape."""
    wa, code, held = _ctx()
    expect = {
        "actionspace": ["action", "space"],
        "hashmap": ["hash", "map"],
        "keyboard": ["key", "board"],
        "blackbird": ["black", "bird"],
        "acceptencoding": ["accept", "encoding"],
        "actionoriented": ["action", "oriented"],
    }
    for word, parts in expect.items():
        assert md.decompose(wa.s, word, code, held)["parts"] == parts, word


def test_mdl_beats_greedy_longest():
    """The compression selector fixes the greedy failure: 'actionspace' reads
    action|space (least bits), NOT the greedy actions|pace."""
    wa, code, held = _ctx()
    r = md.decompose(wa.s, "actionspace", code, held)
    assert r["parts"] == ["action", "space"]
    # the chosen reading is the minimum-bits one among the candidates
    best = min(r["candidates"], key=lambda c: md.candidate_bits(c[1], code))
    assert r["parts"] == list(best[1])


def test_a_lexicalised_token_stays_whole():
    """A form the agent has actually READ as a unit (in its corpus) is cheaper
    whole than split — its own compression selector keeps it whole (honest:
    decomposition fires for NON-lexicalised forms)."""
    wa, code, held = _ctx()
    assert md.decompose(wa.s, "understand", code, held)["parts"] == ["understand"]


# ---------------------------------------------------------------------------
# the DECISION is graph-resident + the decomposition lands as graph data
# ---------------------------------------------------------------------------

def test_decision_is_the_graph_argmin_term():
    """The winning reading is picked by the seeded Argmin Term over the stamped
    DecompCandidate nodes — not a Python min."""
    wa, code, held = _ctx()
    md.decompose(wa.s, "keyboard", code, held)
    cands = [c for c in wa.s.nodes("DecompCandidate")
             if wa.s.node(c)["attrs"].get("for_word") == "keyboard"]
    assert len(cands) >= 2                      # several readings were built
    winner = wa.s._inner.evaluate(md._argmin_bits_term(), {})
    # re-stamp keyboard's candidates active (decompose deactivates on next call) —
    # here keyboard was the last decompose, so its candidates are still active
    bits = {str(c): wa.s.node(c)["attrs"]["bits"] for c in cands}
    assert str(winner) in bits
    assert bits[str(winner)] == min(bits.values())


def test_decomposition_emits_has_part_graph():
    wa, code, held = _ctx()
    md.decompose(wa.s, "blackbird", code, held)
    comp = [n for n in wa.s.nodes("CompoundForm")
            if wa.s.node(n)["attrs"].get("surface") == "blackbird"][-1]
    parts = [wa.s.node(m)["attrs"]["surface"]
             for m in wa.inner.neighbours(comp, "has_part")]
    assert parts == ["black", "bird"]


def test_agent_records_its_decision_spec():
    wa, code, held = _ctx()
    specs = wa.s.nodes("DecompositionSpec")
    assert specs
    a = wa.s.node(specs[-1])["attrs"]
    assert "minimum description length" in a.get("selector", "")
    assert a.get("decision_term") == "Argmin(DecompCandidate, c, bits)"

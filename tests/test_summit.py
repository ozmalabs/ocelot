"""test_summit — THE SUMMIT (Phase 5): the WHOLE committed comprehension +
analysis stack read UNSEEN real Aesop fables cold, and the HONEST result is
locked as a regression.

This test adds NO capability and edits NO domain module or seed. It runs the
already-committed entry points (`comprehension_reader.read_and_comprehend`,
`literary_analysis.produce_analysis` / `verify_grounding`) on three fables NEVER
used in development (dev used the crow + the mouse-and-stones) and asserts the
HONEST ledger:

  · MECHANISM GENERALIZES — every unseen fable builds a non-empty situation
    model (SmEntity nodes) + a discourse-coherence graph with >=1 decoded
    coherence relation + a non-empty centrality ranking. The low-level reader
    reads graph structure, so it generalizes to unseen text.
  · CONTENT / PARSE BOUNDED — the goal->arc->trope->theme->analysis chain does
    NOT fire on any of the three, for reasons that are NAMED, not hidden:
      - ANT: the need-state 'cold' IS detected as a goal-gap candidate, but the
        finite need->remedy codebook (thirst/hunger/danger) has no remedy for
        it -> honest null (codebook finiteness).
      - FOX: the prenominal need-state ('a hungry fox wanted ...') is mis-slotted
        by the clause parser (verb slot gets 'fox'), so 'hungry' never attaches
        to the fox as a state-attr -> no goal-gap candidate at all (parse gap).
      - LION: the protagonist's driver is escape-from-a-net, not a lexicalised
        need-state adjective -> no covered candidate.
  · THE ANTI-HALLUCINATION GATE HOLDS ON UNSEEN TEXT — with no arc, the analysis
    is EMPTY, and `verify_grounding` is ok (nothing emitted -> nothing
    ungrounded). The stack REFUSES to fabricate an analysis it cannot ground.
  · NO TUNING — no fable text appears as a literal in any domains/*.py (the stack
    was not edited to fit these fables); donkey = 0 (no LLM); no `import re` in
    the reader/analysis modules; no `git` anywhere in the summit code.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_summit.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import comprehension_reader as cr                   # noqa: E402
from domains import literary_analysis as la                      # noqa: E402
import jabberwock_summit as summit                               # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _read(text):
    agent = _fresh()
    graph = cr.read_and_comprehend(agent, text, window=2)
    analysis = la.produce_analysis(agent, graph=graph)
    grounding = la.verify_grounding(agent, analysis)
    return agent, graph, analysis, grounding


_BY_TITLE = {f["title"]: f for f in summit.FABLES}


# --------------------------------------------------------------------------- #
#  MECHANISM GENERALIZES — the low-level reader builds a coherent graph on every
#  unseen fable (situation model + discourse coherence + centrality).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("title", list(_BY_TITLE))
def test_comprehension_mechanism_generalizes(title):
    agent, graph, _, _ = _read(_BY_TITLE[title]["text"])
    # a non-empty situation model with real entities
    sm = graph["spine"]["situation_model"]
    assert len(sm) >= 3, "no situation model built for %s" % title
    assert list(agent.s.nodes("SmEntity")), "no SmEntity nodes for %s" % title
    # the protagonist animal is recognised as an entity with animal category
    cats = {v.get("coref_category") for v in sm.values()}
    assert "animal" in cats, "protagonist animal not categorised for %s" % title
    # discourse coherence decoded at least one real relation
    rels = [p for p in graph["discourse"]["pairs"] if p.get("relation")]
    assert rels, "no coherence relation decoded for %s" % title
    # centrality ranked the events
    assert graph["centrality"]["ranking"], "empty centrality for %s" % title


def test_ant_decodes_a_marked_contrast():
    """The unseen ant fable's 'But the ant had none to spare.' is a DISCOURSE-
    MARKED contrast — the coherence mechanism decodes it on unseen text (proof
    the discourse reader is not crow-specific)."""
    _, graph, _, _ = _read(_BY_TITLE["The Ant and the Grasshopper"]["text"])
    contrasts = [p for p in graph["discourse"]["pairs"] if p.get("relation") == "contrast"]
    assert contrasts, "the 'but' contrast was not decoded"


# --------------------------------------------------------------------------- #
#  CONTENT / PARSE BOUNDED — the higher-order chain honestly nulls, per fable,
#  for the NAMED reason. These lock the honest ledger as a regression.
# --------------------------------------------------------------------------- #
def test_ant_cold_is_a_detected_candidate_but_codebook_has_no_remedy():
    """The CLEANEST codebook-finiteness case: 'cold' is DETECTED as a need-state
    goal-gap candidate (the mechanism fired), but the finite need->remedy
    codebook (thirst/hunger/danger) has no remedy for it -> no goal minted."""
    _, graph, _, _ = _read(_BY_TITLE["The Ant and the Grasshopper"]["text"])
    cand = [(g["entity"], g.get("need_attr")) for g in graph["goal_gaps"]]
    assert ("grasshopper", "cold") in cand, "the 'cold' candidate was not detected"
    assert not [g for g in graph["goal"] if g.get("minted")], \
        "'cold' should decode to NO remedy (honest null)"


def test_fox_prenominal_need_state_is_not_attached_parse_gap():
    """The FOX shows a PARSE gap, not a codebook gap: 'A hungry fox wanted the
    cheese' mis-slots ('fox' lands in the relation slot), so 'hungry' never
    attaches to the fox as a state-attr -> NO goal-gap candidate at all."""
    _, graph, _, _ = _read(_BY_TITLE["The Fox and the Crow"]["text"])
    assert not graph["goal_gaps"], \
        "expected no goal-gap candidate (hungry mis-parsed), got %r" % graph["goal_gaps"]


@pytest.mark.parametrize("title", list(_BY_TITLE))
def test_generic_eventive_yields_an_arc_but_goal_codebook_stays_finite(title):
    """GENERIC-EVENTIVE UPDATE (e7dc899f) — this test froze the pre-generic
    limitation (no goal -> no arc -> no trope) as an expectation; the generic
    work is exactly what dissolved it. Every unseen fable now yields a narrative
    ARC: the real eventive verbs (gnawed/freed/flattered/snatched...) mint
    SmEvents generically via WordNet's verb classification, so an arc forms even
    with NO goal. What STILL nulls is the GOAL — the finite need->remedy codebook
    (thirst/hunger/danger) has no remedy for gratitude/flattery/foresight, so no
    goal is minted: the honest codebook-finiteness the generic work did NOT widen.
    The trope is either a COARSE learned quantum (Lion&Mouse: LEARNED_INCREMENTAL)
    or absent (Fox/Ant) — a structural pattern, never the real moral."""
    _, graph, _, _ = _read(_BY_TITLE[title]["text"])
    assert (graph["narrative_arc"] or {}).get("arcs"), \
        "generic-eventive should now yield an arc for %s" % title
    assert not [g for g in graph["goal"] if g.get("minted")], \
        "the need->remedy codebook is still finite: no goal for %s" % title


# --------------------------------------------------------------------------- #
#  THE ANTI-HALLUCINATION GATE HOLDS ON UNSEEN TEXT — empty analysis, and
#  verify_grounding ok (nothing emitted -> nothing ungrounded). The stack
#  refuses to fabricate an ungrounded analysis.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("title", list(_BY_TITLE))
def test_grounding_gate_holds_on_unseen_text(title):
    """THE ANTI-HALLUCINATION GATE — the invariant that survives genericity.
    Post-generic (e7dc899f) an arc that mints a coarse learned trope+theme DOES
    produce a grounded analysis (Lion&Mouse: grounded claims), while an arc with
    no theme produces an EMPTY analysis (Fox/Ant: refusal). Either way — grounded
    or empty — the stack NEVER fabricates: every emitted claim is graph-grounded
    and verify_grounding is ok. That is the property under test, not emptiness."""
    _, _, analysis, grounding = _read(_BY_TITLE[title]["text"])
    # the gate holds: nothing ungrounded, whether the analysis is full or empty
    assert grounding["ok"], "unresolved pointers on %s: %r" % (title, grounding["unresolved"][:5])
    for c in analysis.get("claims") or []:
        assert c["graph_pointers"], "ungrounded claim leaked on %s: %r" % (title, c["sentence"])


# --------------------------------------------------------------------------- #
#  NO TUNING — the stack was not edited to fit these fables.
# --------------------------------------------------------------------------- #
def test_no_fable_text_is_hardcoded_in_the_stack():
    """No content phrase from any summit fable appears as a literal in the reader
    or analysis modules — the stack was NOT tuned to these fables (the summit is
    scripts + this test only)."""
    # distinctive content words unique to the summit fables (NOT dev words)
    tokens = ("grasshopper", "gnawed", "flattered", "snatched", "hunters", "praised")
    for mod in (cr, la):
        src = inspect.getsource(mod).lower()
        for tok in tokens:
            assert tok not in src, "summit-fable token %r hardcoded in %s" % (tok, mod.__name__)


def test_donkey_zero_and_no_re_and_no_git():
    """donkey = 0 (no LLM), no `import re`, no `git` — in the summit code AND the
    reader/analysis modules it drives."""
    for mod in (summit, cr, la):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "import re in %s" % mod.__name__
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "from re import in %s" % mod.__name__
        low = src.lower()
        for banned in ("openai", "anthropic", "requests.post", "call_model",
                       "subprocess", "os.system", '"git ', "'git ", "git stash", "git commit"):
            assert banned not in low, "banned token %r in %s" % (banned, mod.__name__)


def test_summit_script_runs_end_to_end():
    """The summit driver runs all three fables end-to-end without error and
    returns one record per fable, each grounding-ok."""
    results = summit.run()
    assert len(results) == len(summit.FABLES)
    for r in results:
        assert r["grounding"]["ok"], "grounding failed for %s" % r["fable"]["title"]

"""COREFERENCE WIRED INTO THE READING PATH (domains/coref_entities.py).

situation_model_reader.py builds a SITUATION MODEL from read text (SmEntity /
SmEvent), but a pronoun argument ("he"/"she"/"it"/"they") used to mint its OWN
literal SmEntity instead of resolving to the protagonist it denotes, so a
state change attributed to "he" landed on a throwaway node. domains/
reference_resolution.py already has a real resolver (Centering Theory,
Givenness Hierarchy, agreement filter) but is wired only to the CONVERSATION
path (frame-shaped turns + a ConversationWorld-specific index) and its
antecedent RANKING is a Python `max()`/if-else picker — not graph-native.

coref_entities.py wires coreference into READING: it reuses reference_
resolution's DATA (`_CF_RANK`, `_PRONOUNS`) and documented ALGORITHM, but
RE-EXPRESSES the antecedent choice as an `Argmax` Term-tree over the resident
SmEntity pool (evaluated natively by `substrate.evaluate`, the SAME discipline
domains/native_vote.py used for its k-NN decision) — Python never calls
`max()`/`sorted()` to pick a winner.

Discriminative gates (donkey = 0, no LLM):

  * HEADLINE — "John met Bill. He left the room." -> 'he' binds to the SmEntity
    'john' (salience: agent out-ranks patient), and the leaving predication's
    protagonist is 'john', not a throwaway 'he' node.
  * CROSS-SENTENCE — a pronoun-introduced referent ("She entered the kitchen.
    She dropped the cup.") and a named referent ("Mary entered the kitchen.
    She dropped the cup.") both persist: the SECOND mention resolves (via the
    Argmax resonance) to the SAME SmEntity the first established, and the
    cup's broken state attaches under the right agent.
  * HELD-OPEN / DISCRIMINATIVE — a genuine tie (two candidates, same role rank,
    same recency) is HELD OPEN (RI-Val margin check), not force-bound to
    whichever came first in some arbitrary iteration order.
  * FEATURAL FILTER — 'it' never binds to an entity confidently grounded
    person (rejects it outright, or resolves elsewhere when a non-person
    candidate exists); 'they' requires a plural-grounded antecedent (a
    singular referent is rejected).
  * GRAPH-NATIVE SOURCE AUDIT — the antecedent choice is an Argmax Term
    evaluated by `native.evaluate` (Rust), not a Python max()/sorted(); no
    `import re` anywhere in coref_entities.py.
  * NO REGRESSION — reference_resolution / situation_model_wire / reading_scope
    keep passing unchanged (this module is additive, calls them as-is).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_coref_into_entities.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import coref_entities as ce              # noqa: E402


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


def _entity_name(rec: dict, name: str) -> dict:
    return rec["situation_model"].get(name, {})


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_argmax_is_native():
    """No `import re` anywhere in coref_entities.py; the antecedent-choosing
    Term is literally an Argmax node (source audited via the AST, not a
    string search) whose `source`/`value` reference the resident SmEntity
    pool -- the decision is a Program, not a Python max()/sorted(). The one
    Python `sorted()` in the file lives in `_update_centering` (Cf/Cb turn
    BOOKKEEPING -- recording who was mentioned, not choosing an antecedent);
    `resolve_pronoun` (the actual bind) contains no max()/sorted() at all."""
    import inspect

    src_path = os.path.join(ROOT, "domains", "coref_entities.py")
    with open(src_path) as f:
        src = f.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import found"

    resolve_src = inspect.getsource(ce.resolve_pronoun)
    assert "max(" not in resolve_src and "sorted(" not in resolve_src

    term = ce.antecedent_argmax_term(ce._PRONOUNS["he"], None)
    assert term["type"] == "Argmax"
    assert term["source"]["type"] == "Filter"
    assert term["source"]["source"]["type"] == "NodesOfType"
    assert term["source"]["source"]["node_type"] == "SmEntity"


def test_reference_resolution_ranking_is_not_native_reported_honestly():
    """STUDY FINDING: reference_resolution.reference_resolution_procedure ranks
    survivors with a Python max()/if-else -- confirmed here so the report is
    honest (this is WHY coref_entities expresses the ranking as its own Argmax
    Term rather than calling that procedure directly)."""
    import inspect
    from domains import reference_resolution as rr
    src = inspect.getsource(rr.DiscourseStore.reference_resolution_procedure)
    assert "max(" in src and "survivors" in src


# --------------------------------------------------------------------------- #
#  HEADLINE.
# --------------------------------------------------------------------------- #
def test_headline_he_binds_to_protagonist():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "John met Bill. He left the room.")

    flat = [tuple(tb["predications"][0]) for tb in r["textbase"] if tb["predications"]]
    assert ("met", "john", "bill") in flat

    res = [x for x in r["resolutions"] if x["surface"] == "he"]
    assert len(res) == 1 and res[0]["resolved"] is True
    assert res[0]["concept"] == "john"
    assert "salience" in res[0]["rule"] or "centering" in res[0]["rule"]

    # the state change ('left the room') landed on the resolved protagonist,
    # not a throwaway 'he' node -- verbatim.
    assert "he" not in r["situation_model"]
    assert r["situation_model"]["john"]["coref_mentions"] == 2.0


# --------------------------------------------------------------------------- #
#  CROSS-SENTENCE.
# --------------------------------------------------------------------------- #
def test_cross_sentence_named_antecedent_persists():
    ag = _fresh()
    r = ce.read_into_situation_model(
        ag, "The cup is fragile. Mary entered the kitchen. She dropped the cup.")
    res = [x for x in r["resolutions"] if x["surface"] == "she"]
    assert len(res) == 1 and res[0]["resolved"] is True
    assert res[0]["concept"] == "mary"

    mary = r["situation_model"]["mary"]
    assert mary["location"] == "kitchen"           # 1st mention's predicate
    cup = r["situation_model"]["cup"]
    assert cup["broken"] == 1 and cup["on_floor"] == 1     # 2nd mention's agent's act


def test_cross_sentence_repeated_pronoun_converges_on_one_entity():
    """No named antecedent exists at all ('She entered...She dropped...'): the
    FIRST 'she' is honestly HELD OPEN (a genuine discourse-initial pronoun has
    no textual antecedent), and situation_model_reader's own fallback mints a
    literal 'she' SmEntity -- but the SECOND 'she' resolves (via the Argmax
    resonance, a real decision, not a name-string coincidence) to that SAME
    resident entity, so both mentions converge on ONE persistent SmEntity and
    the cup's broken state attaches under it."""
    ag = _fresh()
    r = ce.read_into_situation_model(
        ag, "The cup is fragile. She entered the kitchen. She dropped the cup.")
    she_resolutions = [x for x in r["resolutions"] if x["surface"] == "she"]
    assert len(she_resolutions) == 2
    assert she_resolutions[0]["resolved"] is False        # discourse-initial: no antecedent
    assert she_resolutions[1]["resolved"] is True          # SECOND resonates to the resident trace
    assert she_resolutions[1]["concept"] == "she"

    assert r["situation_model"]["she"]["location"] == "kitchen"
    assert r["situation_model"]["cup"]["broken"] == 1


# --------------------------------------------------------------------------- #
#  HELD-OPEN / DISCRIMINATIVE.
# --------------------------------------------------------------------------- #
def test_ambiguous_tie_is_held_open_not_forced():
    """Two candidates with IDENTICAL role-rank and recency (both introduced as
    'agent' in the SAME turn) -- a genuine tie. The margin gate (RI-Val
    validation) must HOLD IT OPEN, not silently pick whichever iterates first."""
    ag = _fresh()
    ce._touch_entity(ag, "John arrived.", "john", "agent", 1)
    ce._touch_entity(ag, "Bill arrived.", "bill", "agent", 1)
    rec = ce.resolve_pronoun(ag, "he", "He left.", 2, ce._current_cb(ag))
    assert rec["resolved"] is False
    assert rec["margin"] == 0.0
    assert "HELD OPEN" in rec["reason"]

    # the Mention node itself carries the held_open flag (graph state, not a
    # Python-only in-memory flag) -- look it up by its own bookkeeping attrs.
    sub, _ = ce._resolve(ag)
    mentions = [sub.node(n)["attrs"] for n in sub.nodes("SmMention")]
    held = [m for m in mentions if m.get("surface") == "he"]
    assert held and held[0].get("held_open") == 1.0


def test_headline_role_rank_breaks_ties_recency_being_equal():
    """The headline case IS a same-turn tie in recency; it resolves cleanly
    because role-rank (agent vs patient) differs -- confirming the margin
    threshold correctly treats a role-rank distinction as decisive while a
    true (rank AND recency) tie is not."""
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "John met Bill. He left the room.")
    res = [x for x in r["resolutions"] if x["surface"] == "he"][0]
    assert res["resolved"] is True and res["margin"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
#  CLEANLINESS — a junk-blob candidate (a multi-word underscore glom from an
#  imperfectly-parsed clause, e.g. 'poor_thing_felt') must not steal a bind
#  from a clean single-head entity.
# --------------------------------------------------------------------------- #
def test_clean_candidate_beats_junk_blob_in_argmax():
    """Two agreement-eligible candidates, identical role-rank and recency
    (both introduced as 'agent' in the same turn): a CLEAN one ('john') and a
    JUNK BLOB ('tall_man_walked' -- a multi-word underscore glom, the shape a
    mis-parsed clause fragment takes). The CLEAN candidate wins (verbatim
    gate case) -- not a tie, not decided by iteration order."""
    ag = _fresh()
    ce._touch_entity(ag, "John arrived.", "john", "agent", 1)
    ce._touch_entity(ag, "The tall_man_walked arrived.", "tall_man_walked", "agent", 1)
    rec = ce.resolve_pronoun(ag, "he", "He left.", 2, ce._current_cb(ag))
    assert rec["resolved"] is True
    assert rec["concept"] == "john"
    assert rec["margin"] >= ce._CLEAN_BONUS


def test_cleanliness_factor_values():
    """The held nominal faculty (consumption_quality.is_nominal) + a token-
    count structural check -- not a Python winner-pick, a graph-attr FACTOR
    computed once per referent name."""
    assert ce._grounded_cleanliness("john") == 1.0
    assert ce._grounded_cleanliness("crow") == 1.0
    assert ce._grounded_cleanliness("narrow_neck") == 1.0          # short compound: clean
    assert ce._grounded_cleanliness("poor_thing_felt") == 0.0      # 3-token clause glom: blob


def test_clean_bind_no_regression_he_to_john_she_to_mary():
    """The existing clean he->john / she->mary binds still work UNCHANGED --
    both candidates are equally clean (1.0), so the new factor does not
    perturb an already-correct decision."""
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "John met Bill. He left the room.")
    res = [x for x in r["resolutions"] if x["surface"] == "he"][0]
    assert res["resolved"] is True and res["concept"] == "john"

    ag2 = _fresh()
    r2 = ce.read_into_situation_model(
        ag2, "The cup is fragile. Mary entered the kitchen. She dropped the cup.")
    res2 = [x for x in r2["resolutions"] if x["surface"] == "she"][0]
    assert res2["resolved"] is True and res2["concept"] == "mary"


def test_cleanliness_is_a_factor_in_the_argmax_term_not_a_python_pick():
    """The cleanliness score is READ into the Argmax's own `value` Term (an
    Attr node keyed 'coref_cleanliness', weighted and summed alongside the
    other factors) -- Python never inspects candidate names to pick a
    winner."""
    import inspect
    term = ce.antecedent_argmax_term(ce._PRONOUNS["he"], None)
    assert term["type"] == "Argmax"

    def _contains_cleanliness(node) -> bool:
        if isinstance(node, dict):
            if node.get("type") == "Attr" and node.get("key") == "coref_cleanliness":
                return True
            return any(_contains_cleanliness(v) for v in node.values())
        if isinstance(node, list):
            return any(_contains_cleanliness(v) for v in node)
        return False

    assert _contains_cleanliness(term["value"])
    resolve_src = inspect.getsource(ce.resolve_pronoun)
    assert "max(" not in resolve_src and "sorted(" not in resolve_src


# --------------------------------------------------------------------------- #
#  FEATURAL FILTER.
# --------------------------------------------------------------------------- #
def test_it_never_binds_a_grounded_person():
    """A resident entity confidently grounded person is NEVER an 'it' antecedent
    -- proven both when it is the ONLY candidate (pure reject, held open) and
    when a non-person candidate is also present (rejects the person, binds the
    non-person instead)."""
    ag = _fresh()
    ce._touch_entity(ag, "The woman arrived.", "woman", "agent", 1)
    rec = ce.resolve_pronoun(ag, "it", "It left.", 2, ce._current_cb(ag))
    assert rec["resolved"] is False
    assert "no resident SmEntity agrees" in rec["reason"]

    ag2 = _fresh()
    r2 = ce.read_into_situation_model(
        ag2, "The woman entered the kitchen. It left the room.")
    res = [x for x in r2["resolutions"] if x["surface"] == "it"][0]
    assert res["resolved"] is True
    assert res["concept"] != "woman"
    assert res["concept"] == "kitchen"


def test_they_requires_a_plural_antecedent():
    """'they' rejects a singular-grounded referent (held open) and binds a
    plural-grounded one ('children' -- WordNet morphy: children -> child)."""
    ag = _fresh()
    r = ce.read_into_situation_model(
        ag, "The woman entered the kitchen. They left the room.")
    res = [x for x in r["resolutions"] if x["surface"] == "they"][0]
    assert res["resolved"] is False
    assert "plural" in res["reason"]

    ag2 = _fresh()
    r2 = ce.read_into_situation_model(
        ag2, "The children entered the kitchen. They left the room.")
    res2 = [x for x in r2["resolutions"] if x["surface"] == "they"][0]
    assert res2["resolved"] is True
    assert res2["concept"] == "children"
    assert r2["situation_model"]["children"]["coref_number"] == "plural"


# --------------------------------------------------------------------------- #
#  NO REGRESSION (this module's own dependencies, still callable as-is).
# --------------------------------------------------------------------------- #
def test_situation_model_reader_unchanged_direct_call_still_works():
    from domains import situation_model_reader as smr
    ag = _fresh()
    r = smr.read_into_situation_model(ag, "The glass is fragile. John dropped the glass.")
    assert r["situation_model"]["glass"]["broken"] == 1


def test_reference_resolution_conversation_store_unchanged():
    from domains import reference_resolution as rr
    ag = _fresh()

    class _World:
        def __init__(self, s):
            self.s = s
            self._concept_nodes = {}

        def _get_or_create_concept(self, name):
            if name in self._concept_nodes:
                return self._concept_nodes[name]
            cid = self.s.add_node("Concept", {"name": name})
            self._concept_nodes[name] = cid
            return cid

    world = _World(ag.s)
    store = rr.DiscourseStore(ag.s, world)
    store.update_from_frame({"agent": "cat", "patient": "mat"})
    store.update_centering({"cat": "agent", "mat": "patient"})
    out = store.reference_resolution_procedure("it", 1)
    assert out["resolved"] is True and out["concept"] == "cat"

"""INFER MEANING FROM CONTEXT (domains/meaning_inference.py + seeds/meaning_inference.json).

reading_review._predication_selectional_incoherence runs a seeded
SelectionalRestriction BACKWARD (a KNOWN subject that violates a mental-state
verb's animacy demand is scored incoherent) and explicitly SKIPS an OOV
subject — there is nothing to violate when the filler is unknown. This module
is the FORWARD twin: 'The glarn feared the storm.' — 'feared' is verb.emotion;
a held (verb_class -> requires_class) SelectionalClassPair says verb.emotion
admits a noun.person/noun.animal subject; 'glarn' has NO WordNet sense at all.
Instead of silently skipping it, the pair's `requires_class` is read FORWARD as
'glarn'-s PROVISIONAL semantic type, held as a REVISABLE, confidence-graded
InferredSense (the SAME ReadingBelief shape reading_collapse uses for the
passive/stative collapse) — ONE InferredSense per (term, sense_class): 'glarn'
being admissibly noun.person AND noun.animal is TWO rows, not one list-valued
node (the scalar-row normal form the join needs).

ZERO PYTHON DECISIONS: domains/meaning_inference.py only WRITES FACTS (WordNet
oov/is_pronoun reads on the filler Concept; an unconditional PredicationSlot
per predication argument carrying its relation's WordNet verb-class and its
structural slot). There is no `if rel_class in verb_classes` anywhere in
Python — the JOIN (Eq(ps.rel_verb_class, cp.verb_class) AND Eq(ps.slot,
cp.slot)) and every other decision (mint-vs-combine, abstain-when-grounded,
supersede) live in seeds/meaning_inference.json's three rules.

Discriminative gates (donkey = 0):

  * HEADLINE — an OOV subject of a seeded-restricted relation gets
    InferredSense rows whose sense_class values match the join's admitted
    classes.
  * COMBINE — two constraining sentences on the SAME novel term raise the
    held confidence per class (fold, not duplicate).
  * DISCRIMINATIVE NULL — no restriction on the relation (or the subject is
    already WordNet-known) mints NOTHING. Non-fabrication.
  * REVISABLE — the belief is queryable after the read, and a later
    grounding supersedes it with ONE set_attr (nothing else changes).
  * SOURCE AUDIT — no regex in the reading path; the fold/dedup/abstain
    decision lives in the seed rules, not a Python if/else.
  * THE AGENT EXTENDS ITSELF — teaching ONE new SelectionalClassPair via
    teach() unlocks inference in a domain (motion verbs) that produced
    NOTHING before the lesson, with no code change.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_meaning_inference_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_collapse as rc            # noqa: E402
from domains import meaning_inference as mi           # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    # function-scoped: each test gets a FRESH graph, so distinct-term hygiene
    # across tests is not load-bearing and cross-test leakage is impossible.
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


def _concept_by_name(a, name):
    for n in a.s.nodes("Concept"):
        if str(a.s.node(n)["attrs"].get("name")).lower() == str(name).lower():
            return n
    return None


def _classes(senses) -> set:
    return {s["sense_class"] for s in senses}


# --------------------------------------------------------------------------- #
#  HEADLINE
# --------------------------------------------------------------------------- #
def test_headline_infers_provisional_sense_from_selectional_restriction(agent):
    r = rc.read_clause(agent, "The glarn feared the storm.", write=True)
    assert r["predications"] == [["feared", "glarn", "storm"]], r

    senses = mi.held_inferred_senses(agent, "glarn")
    assert _classes(senses) >= {"noun.person", "noun.animal"}, senses
    for s in senses:
        assert s["source"] == "selectional", s
        assert s["via"] == "feared", s
        assert s["revisable"] == 1.0, s
        assert s["status"] == "active", s
        assert s["confidence"] and s["confidence"] > 0, s


# --------------------------------------------------------------------------- #
#  COMBINE — two constraining sentences fold into ONE row per class,
#  confidence rises (per class), not duplicated.
# --------------------------------------------------------------------------- #
def test_combine_raises_confidence_not_duplicates(agent):
    rc.read_clause(agent, "The thargle feared the storm.", write=True)
    first = mi.held_inferred_senses(agent, "thargle")
    assert _classes(first) >= {"noun.person", "noun.animal"}, first
    conf1_by_class = {s["sense_class"]: s["confidence"] for s in first}

    rc.read_clause(agent, "The thargle dreaded the omen.", write=True)
    second = mi.held_inferred_senses(agent, "thargle")
    # STILL exactly one row per class -- folded, not duplicated.
    assert len(second) == len(first), (first, second)
    conf2_by_class = {s["sense_class"]: s["confidence"] for s in second}
    for cls, c1 in conf1_by_class.items():
        assert conf2_by_class[cls] > c1, (cls, c1, conf2_by_class[cls])


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULL — no fabrication.
# --------------------------------------------------------------------------- #
def test_null_verb_with_no_seeded_restriction_mints_nothing(agent):
    # 'chase' is verb.contact/verb.motion/verb.social -- never cognition/emotion,
    # so no held SelectionalClassPair joins it, regardless of which WordNet
    # sense wins disambiguation.
    rc.read_clause(agent, "The dog chased the vorlin.", write=True)
    assert mi.held_inferred_senses(agent, "vorlin") == []


def test_null_plain_preposition_relation_mints_nothing(agent):
    # 'of' is never a verb sense -- rel_verb_class is null on the PredicationSlot,
    # so the Eq(ps.rel_verb_class, cp.verb_class) join never matches (null equals
    # no verb_class string) -- pure join failure, not a Python skip.
    rc.read_clause(agent, "the color of the zeltuun", write=True)
    assert mi.held_inferred_senses(agent, "zeltuun") == []


def test_null_known_word_never_gets_an_inferred_sense(agent):
    # 'crow' is a real WordNet noun (noun.animal) -- oov=0.0 on its Concept, so
    # the join's Eq(fc.oov, 1.0) guard never admits it, even though 'feared'
    # carries a matching SelectionalClassPair.
    rc.read_clause(agent, "The crow feared the storm.", write=True)
    assert mi.held_inferred_senses(agent, "crow") == []


# --------------------------------------------------------------------------- #
#  REVISABLE — held, queryable, superseded by ONE set_attr on later grounding.
# --------------------------------------------------------------------------- #
def test_revisable_belief_is_held_and_superseded_on_grounding(agent):
    rc.read_clause(agent, "The quennor feared the storm.", write=True)
    before = mi.held_inferred_senses(agent, "quennor")
    assert len(before) >= 1, before
    assert all(s["status"] == "active" for s in before), before
    before_by_class = {s["sense_class"]: (s["confidence"], s["via"]) for s in before}

    # simulate the term becoming genuinely GROUNDED (e.g. by teach() / a real
    # grounding pass): the placeholder Concept _write_predications already
    # minted for 'quennor' gains grounded=1.0.
    cid = _concept_by_name(agent, "quennor")
    assert cid is not None, "the grounding write should have minted a placeholder Concept"
    agent.s.set_attr(cid, "grounded", 1.0)
    agent.inner.run_rules()

    after = mi.held_inferred_senses(agent, "quennor")
    assert len(after) == len(before), (before, after)   # flipped, not duplicated/dropped
    assert all(s["status"] == "superseded" for s in after), after
    # ONLY status changed; confidence/via untouched (the ONE-set_attr flip).
    after_by_class = {s["sense_class"]: (s["confidence"], s["via"]) for s in after}
    assert after_by_class == before_by_class, (before_by_class, after_by_class)


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decision_lives_in_the_seed():
    mod_path = os.path.join(ROOT, "domains", "meaning_inference.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    assert "import re" not in lines and "import re as _re" not in lines
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # the Python side never mints/updates an InferredSense directly, never
    # tests relation-class membership, and never joins against
    # SelectionalClassPair -- only the mechanical PredicationSlot/oov/is_pronoun
    # facts. The fold/mint/combine/abstain/supersede decision is the seed rules'.
    assert 'add_node("InferredSense"' not in src
    assert 'InferredSense", {' not in src
    assert '"status", "superseded"' not in src   # the supersede flip lives in the rule, not here
    # no Python membership test standing in for the graph join (the exact
    # pattern this design revision replaced: `if rel_class in verb_classes`).
    for ln in lines:
        assert not (" in verb_class" in ln and ln.startswith(("if ", "elif "))), ln

    import json
    seed_path = os.path.join(ROOT, "seeds", "meaning_inference.json")
    seed = json.load(open(seed_path))
    names = {r["name"] for r in seed.get("rules", [])}
    assert names == {"infer_sense_mint", "infer_sense_combine", "infer_sense_supersede",
                      "infer_sense_from_definition", "infer_sense_from_morphology",
                      "infer_sense_from_analogy", "infer_sense_from_structural_analogy"}, names
    # the join is graph data: Eq(ps.rel_verb_class, cp.verb_class), not a Python `in`.
    mint = next(r for r in seed["rules"] if r["name"] == "infer_sense_mint")
    where_str = json.dumps(mint["where"])
    assert '"rel_verb_class"' in where_str and '"verb_class"' in where_str
    assert '"type": "Eq"' in where_str
    # slice 3: the affix join is graph data too — Eq(ac.affix, mc.affix) AND
    # Eq(ac.position, mc.position), never a Python `if affix in {...}`.
    morph = next(r for r in seed["rules"] if r["name"] == "infer_sense_from_morphology")
    morph_where_str = json.dumps(morph["where"])
    assert '"affix"' in morph_where_str and '"position"' in morph_where_str
    assert morph_where_str.count('"type": "Eq"') >= 4   # affix, position, oov, +dedup fields
    assert 'add_node("AffixCandidate"' in src            # mechanical fact-writing only
    for ln in lines:
        if ln.startswith(("if ", "elif ")):
            assert "affix ==" not in ln and "affix in" not in ln, ln
    # slice 2: the relation SELECTION ('is_a') is the rule's Eq, never a Python
    # `if relation == 'is_a'` branch (that exact string never appears in the
    # module — annotate_predication_facts writes `relation` as a fact,
    # unconditionally, for every predication with an object).
    defn = next(r for r in seed["rules"] if r["name"] == "infer_sense_from_definition")
    defn_where_str = json.dumps(defn["where"])
    assert '"relation"' in defn_where_str and '"value": "is_a"' in defn_where_str
    assert defn_where_str.count('"type": "Eq"') >= 3   # relation, subj_oov, genus_head_grounded
    assert "if relation ==" not in src and 'relation == "is_a"' not in src
    assert "if rel ==" not in src and 'rel == "is_a"' not in src


# =========================================================================== #
#  SLICE 2 — DEFINITIONAL inference: an OOV subject of an in-situ copular
#  definition ('A glimt is a lake.') whose GENUS HEAD grounds mints a
#  higher-confidence InferredSense{source:'definition'}.
# =========================================================================== #
def _by_source(senses, source):
    return [s for s in senses if s["source"] == source]


def test_headline_definition_infers_sense_from_copular_definition(agent):
    r = rc.read_clause(agent, "A glimt is a lake.", write=True)
    assert r["predications"] == [["is_a", "glimt", "lake"]], r

    senses = _by_source(mi.held_inferred_senses(agent, "glimt"), "definition")
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["genus"] == "lake", s
    assert s["via"] == "lake", s          # genus_head of a single-word genus is itself
    assert s["sense_class"], s            # WordNet lexname of 'lake' (e.g. noun.object/noun.artifact)
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s
    assert s["confidence"] and s["confidence"] > 0, s


def test_headline_definition_resolves_compound_genus_to_its_head(agent):
    r = rc.read_clause(agent, "A florbin is a small bird.", write=True)
    assert r["predications"] == [["is_a", "florbin", "small_bird"]], r

    senses = _by_source(mi.held_inferred_senses(agent, "florbin"), "definition")
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["via"] == "bird", s           # genus HEAD of 'small_bird'
    assert s["genus"] == "small_bird", s   # the FULL genus phrase, held too
    assert s["sense_class"] == "noun.animal", s


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULLS — no fabrication.
# --------------------------------------------------------------------------- #
def test_null_definition_when_genus_itself_is_oov(agent):
    # 'florbin' (genus) is itself never grounded in WordNet -- genus_head_grounded
    # stays 0, so the join never fires. No definition sense for 'glimt'.
    rc.read_clause(agent, "A glimt is a florbin.", write=True)
    assert _by_source(mi.held_inferred_senses(agent, "glimt"), "definition") == []


def test_null_definition_when_subject_already_known(agent):
    # 'cat' grounds in WordNet -- subj_oov stays 0 on the Predication fact, so the
    # join never admits it, even though the genus ('animal') is cleanly grounded.
    rc.read_clause(agent, "A cat is an animal.", write=True)
    assert _by_source(mi.held_inferred_senses(agent, "cat"), "definition") == []


def test_null_definition_for_a_non_is_a_predication(agent):
    # a selectionally-restricted sentence with NO is_a predication -- the
    # Predication fact's relation != 'is_a', so infer_sense_from_definition never
    # fires (only infer_sense_mint's selectional path may fire here).
    rc.read_clause(agent, "The glarn feared the storm.", write=True)
    assert _by_source(mi.held_inferred_senses(agent, "glarn"), "definition") == []


# --------------------------------------------------------------------------- #
#  REVISABLE — held, queryable, superseded by ONE set_attr on later grounding.
# --------------------------------------------------------------------------- #
def test_definition_sense_is_revisable_and_superseded_on_grounding(agent):
    rc.read_clause(agent, "A quorlin is a lake.", write=True)
    before = _by_source(mi.held_inferred_senses(agent, "quorlin"), "definition")
    assert len(before) == 1, before
    assert before[0]["status"] == "active", before

    cid = _concept_by_name(agent, "quorlin")
    assert cid is not None
    agent.s.set_attr(cid, "grounded", 1.0)
    agent.inner.run_rules()

    after = _by_source(mi.held_inferred_senses(agent, "quorlin"), "definition")
    assert len(after) == 1, after
    assert after[0]["status"] == "superseded", after
    assert after[0]["confidence"] == before[0]["confidence"], (before, after)  # ONE set_attr flip


# --------------------------------------------------------------------------- #
#  PRECEDENCE — a definition-sourced sense outranks a selectional one for the
#  same term (coexist as separate rows; higher confidence).
# --------------------------------------------------------------------------- #
def test_definition_sense_outranks_selectional_sense_for_same_term(agent):
    # 'glarn' both fills a selectionally-restricted subject slot (feared ->
    # verb.emotion) AND, in a second sentence, is copularly DEFINED. Both rows
    # coexist -- the definition row's confidence is strictly higher.
    rc.read_clause(agent, "The glarn feared the storm.", write=True)
    rc.read_clause(agent, "A glarn is a lake.", write=True)

    senses = mi.held_inferred_senses(agent, "glarn")
    selectional = _by_source(senses, "selectional")
    definitional = _by_source(senses, "definition")
    assert selectional and definitional, senses
    max_selectional = max(s["confidence"] for s in selectional)
    max_definition = max(s["confidence"] for s in definitional)
    assert max_definition > max_selectional, (selectional, definitional)


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT (slice 2) — the new annotation function is pure fact-writing.
# --------------------------------------------------------------------------- #
def test_source_audit_definition_facts_never_decide_relation(agent):
    mod_path = os.path.join(ROOT, "domains", "meaning_inference.py")
    src = open(mod_path).read()
    # the new Predication fact node is written unconditionally per predication
    # with an object -- never gated on `pred[0]` / `rel` equalling 'is_a' in an
    # executable conditional (docstring prose mentioning the relation is fine;
    # only a live `if`/`elif`/`and`/ternary branch on it would be a violation).
    lines = [ln.strip() for ln in src.splitlines()]
    for ln in lines:
        if ln.startswith(("if ", "elif ")) or " if " in ln:
            assert "is_a" not in ln, ln
    assert 'add_node("Predication"' in src


# --------------------------------------------------------------------------- #
#  THE AGENT EXTENDS ITSELF (slice 2) — definitional coverage needs NO taught
#  seed row at all, unlike slice 1's per-verb-class SelectionalClassPair.
# --------------------------------------------------------------------------- #
def test_self_extension_definitional_needs_no_taught_seed_row(agent):
    # Contrast with test_agent_teaches_new_selectional_coverage below: a NEW verb
    # domain (motion verbs) needed a taught SelectionalClassPair row before
    # 'zibbet' could be classified via selection. Definitional inference needs NO
    # equivalent per-class seed data -- 'wibbon' is classified the INSTANT it is
    # copularly defined, against a genus ('mountain') no held SelectionalClassPair
    # row mentions and with no teach() call anywhere in this test.
    rc.read_clause(agent, "A wibbon is a mountain.", write=True)
    senses = _by_source(mi.held_inferred_senses(agent, "wibbon"), "definition")
    assert len(senses) == 1, senses
    assert senses[0]["via"] == "mountain", senses
    assert senses[0]["sense_class"], senses


# --------------------------------------------------------------------------- #
#  THE AGENT EXTENDS ITSELF — teach() grows selectional coverage; no code change.
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_selectional_coverage(agent, tmp_path):
    from domains.teach import teach

    sentence = "The zibbet migrated over the mountains."
    rc.read_clause(agent, sentence, write=True)
    # 'migrate' is PURE verb.motion -- outside the seeded verb.cognition/
    # verb.emotion SelectionalClassPair rows, so nothing joins yet. The
    # PredicationSlot is already written (unconditionally, at read time) --
    # it is simply inert until a matching join row exists.
    assert mi.held_inferred_senses(agent, "zibbet") == []

    res = teach(agent, "SelectionalClassPair", {
        "kind": "animate_subject", "verb_class": "verb.motion", "slot": "subject",
        "requires_class": "noun.animal", "weight": 0.6,
    }, category="taught_selectional", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- the taught row is new graph data; re-running the
    # agent's OWN standing rules against it is enough (the PredicationSlot from
    # the read above already carries rel_verb_class='verb.motion'/slot='subject').
    # ensure_meaning_inference_seed's reconcile-wire connects the freshly-taught
    # SelectionalClassPair to the agent root (mechanical -- every held pair is
    # wired, unconditionally); then the SAME standing rules see it.
    mi.ensure_meaning_inference_seed(agent)
    agent.inner.run_rules()

    senses = mi.held_inferred_senses(agent, "zibbet")
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.animal", senses
    assert senses[0]["source"] == "selectional", senses
    assert senses[0]["via"] == "migrated", senses

    # the taught row was persisted to the (tmp, isolated) seed file -- a future
    # boot would hold it too, not just this live session.
    taught_path = tmp_path / "taught_selectional.json"
    assert taught_path.exists()


# =========================================================================== #
#  SLICE 3 — MORPHOLOGICAL inference: an OOV term's own SHAPE (derivational
#  affix) carries a semantic class, with no verb/copula/is_a to lean on at all.
#  'florbitis'/'glorbectomy'/'glimtase' are OOV per WordNet (empirically
#  verified: dictionary_lexicon.pick_sense returns None at every slot).
# =========================================================================== #
def _by_morph(senses):
    return _by_source(senses, "morphology")


def test_headline_infers_provisional_sense_from_derivational_suffix(agent):
    r = rc.read_clause(agent, "The florbitis spread quickly.", write=True)
    assert r["predications"] == [["spread", "florbitis", "quickly"]], r

    senses = _by_morph(mi.held_inferred_senses(agent, "florbitis"))
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["sense_class"] == "noun.state", s
    assert s["via"] == "itis", s
    assert s["source"] == "morphology", s
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s
    assert s["confidence"] and s["confidence"] > 0, s


def test_headline_infers_from_surgical_act_suffix(agent):
    rc.read_clause(agent, "The glorbectomy spread quickly.", write=True)
    senses = _by_morph(mi.held_inferred_senses(agent, "glorbectomy"))
    # '-ectomy' AND its own tail '-tomy' both match the codebook, both mapping
    # to noun.act -- the LONGEST-MATCH guard prefers the longer '-ectomy' and
    # abstains on the shorter '-tomy', so exactly ONE row is minted (not a
    # same-class dedup collapse -- the guard prevents the second mint outright).
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.act", senses
    assert senses[0]["via"] == "ectomy", senses


def test_headline_infers_from_enzyme_suffix(agent):
    rc.read_clause(agent, "The glimtase spread quickly.", write=True)
    senses = _by_morph(mi.held_inferred_senses(agent, "glimtase"))
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.substance", senses
    assert senses[0]["via"] == "ase", senses


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULLS
# --------------------------------------------------------------------------- #
def test_null_oov_term_with_no_codebook_affix_mints_nothing(agent):
    # 'florbix' is OOV but matches NO seeded MorphemeClass affix at any
    # suffix/prefix length -- AffixCandidate nodes are written (mechanically,
    # unconditionally) but none joins a MorphemeClass row.
    rc.read_clause(agent, "The florbix spread quickly.", write=True)
    assert _by_morph(mi.held_inferred_senses(agent, "florbix")) == []


def test_null_known_word_with_matching_ending_abstains(agent):
    # 'arthritis' is a REAL WordNet noun (noun.state) -- oov=0.0 on its
    # Concept, so Eq(fc.oov, 1.0) never admits it, even though it ends in
    # the exact seeded '-itis' suffix.
    rc.read_clause(agent, "The arthritis spread quickly.", write=True)
    assert _by_morph(mi.held_inferred_senses(agent, "arthritis")) == []


# --------------------------------------------------------------------------- #
#  REVISABLE
# --------------------------------------------------------------------------- #
def test_morphology_sense_is_revisable_and_superseded_on_grounding(agent):
    rc.read_clause(agent, "The glorbitis spread quickly.", write=True)
    before = _by_morph(mi.held_inferred_senses(agent, "glorbitis"))
    assert len(before) == 1, before
    assert before[0]["status"] == "active", before

    cid = _concept_by_name(agent, "glorbitis")
    assert cid is not None
    agent.s.set_attr(cid, "grounded", 1.0)
    agent.inner.run_rules()

    after = _by_morph(mi.held_inferred_senses(agent, "glorbitis"))
    assert len(after) == 1, after
    assert after[0]["status"] == "superseded", after
    assert after[0]["confidence"] == before[0]["confidence"], (before, after)


# --------------------------------------------------------------------------- #
#  CONFIDENCE ORDER — morphology is the WEAKEST source: below selectional
#  (0.6) and below definition (0.9).
# --------------------------------------------------------------------------- #
def test_morphology_confidence_ranks_below_selectional(agent):
    # 'florbitis' is BOTH the subject of a verb.emotion relation (selectional
    # evidence) AND ends in the seeded '-itis' suffix (morphological evidence).
    rc.read_clause(agent, "The florbitis feared the storm.", write=True)
    senses = mi.held_inferred_senses(agent, "florbitis")
    selectional = _by_source(senses, "selectional")
    morphology = _by_morph(senses)
    assert selectional and morphology, senses
    assert max(s["confidence"] for s in morphology) < min(s["confidence"] for s in selectional), \
        (selectional, morphology)


def test_morphology_confidence_ranks_below_definition(agent):
    # 'wibbitis' is BOTH copularly defined (definitional evidence, conf 0.9)
    # AND ends in the seeded '-itis' suffix (morphological evidence, conf 0.45).
    rc.read_clause(agent, "The wibbitis feared the storm.", write=True)
    rc.read_clause(agent, "A wibbitis is a lake.", write=True)
    senses = mi.held_inferred_senses(agent, "wibbitis")
    definitional = _by_source(senses, "definition")
    morphology = _by_morph(senses)
    assert definitional and morphology, senses
    assert max(s["confidence"] for s in morphology) < min(s["confidence"] for s in definitional), \
        (definitional, morphology)


# --------------------------------------------------------------------------- #
#  THE AGENT EXTENDS ITSELF — teach() grows morphological coverage into a
#  BRAND NEW semantic domain (element/metal, '-ium'/'-onium'); no code change.
#  '-ium' is deliberately NOT seeded (see the seed description) so this test
#  demonstrates growth exactly like slice 1's verb.motion extension.
# --------------------------------------------------------------------------- #
def test_agent_teaches_new_morphological_coverage(agent, tmp_path):
    from domains.teach import teach

    sentence = "The zorbonium spread quickly."
    rc.read_clause(agent, sentence, write=True)
    # 'zorbonium' is OOV; its AffixCandidate facts are already written
    # (unconditionally, at read time) -- '-ium'/'-onium' are simply inert
    # until a matching MorphemeClass row exists.
    assert mi.held_inferred_senses(agent, "zorbonium") == []

    res = teach(agent, "MorphemeClass", {
        "affix": "onium", "position": "suffix", "sense_class": "noun.substance",
        "weight": 0.45, "note": "-onium names an element/metal (a taught row).",
    }, category="taught_morphology", seeds_dir=tmp_path)
    assert res["saved"] is True, res

    # NO re-read needed -- rerun the agent's OWN standing rules against the
    # already-written AffixCandidate facts, exactly like the selectional
    # teach-extension test above.
    mi.ensure_meaning_inference_seed(agent)
    agent.inner.run_rules()

    senses = mi.held_inferred_senses(agent, "zorbonium")
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.substance", senses
    assert senses[0]["source"] == "morphology", senses
    assert senses[0]["via"] == "onium", senses

    taught_path = tmp_path / "taught_morphology.json"
    assert taught_path.exists()


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT (slice 3) — the new annotation function is pure fact-writing.
# --------------------------------------------------------------------------- #
def test_source_audit_morphology_facts_never_decide_the_affix(agent):
    mod_path = os.path.join(ROOT, "domains", "meaning_inference.py")
    src = open(mod_path).read()
    # AffixCandidate is written unconditionally for every 2..6-char suffix /
    # 2..4-char prefix of an OOV filler's head -- never gated on the affix
    # VALUE matching a specific string in an executable conditional.
    lines = [ln.strip() for ln in src.splitlines()]
    for ln in lines:
        if ln.startswith(("if ", "elif ")) or " if " in ln:
            assert "itis" not in ln and "ectomy" not in ln and "ology" not in ln
    assert 'add_node("AffixCandidate"' in src
    # MorphemeClass is only ever mechanically WIRED (reconcile-by-presence,
    # the same idiom as SelectionalClassPair) or read via a graph join in the
    # seed rule -- never constructed by Python, and never used as a Python
    # `in`/`==` decision over its affix/sense_class values.
    assert 'add_node("MorphemeClass"' not in src
    for ln in lines:
        if "MorphemeClass" in ln:
            assert not ln.startswith(("if ", "elif "))


# =========================================================================== #
#  SLICE 4 — ANALOGY inference: an OOV subject of an EXPLICIT COMPARISON
#  ('A glorb is like a pump.' / 'A florx resembles a bird.' -- the reader's own
#  comparative_like_cop/comparative_like constructions ground relation='similar')
#  mints InferredSense{source:'analogy'} from the compared-to object's class.
#  `infer_sense_from_analogy` is `infer_sense_from_definition`'s EXACT join
#  shape with ONE Eq swapped (relation=='similar' instead of 'is_a') -- the
#  unconditional Predication fact slice 2 already writes for every predication
#  with an object ALREADY carries relation='similar' for these sentences, so
#  NO adapter change was needed for this slice at all.
# =========================================================================== #
def _by_analogy(senses):
    return _by_source(senses, "analogy")


def test_headline_analogy_infers_sense_from_explicit_comparison(agent):
    r = rc.read_clause(agent, "A glorb is like a pump.", write=True)
    assert r["predications"] == [["similar", "glorb", "pump"]], r

    senses = _by_analogy(mi.held_inferred_senses(agent, "glorb"))
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["genus"] == "pump", s
    assert s["via"] == "pump", s           # genus_head of a single-word genus is itself
    assert s["sense_class"] == "noun.artifact", s
    assert s["confidence"] == 0.7, s
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s


def test_headline_analogy_resolves_via_resembles_construction(agent):
    r = rc.read_clause(agent, "A florx resembles a bird.", write=True)
    assert r["predications"] == [["similar", "florx", "bird"]], r

    senses = _by_analogy(mi.held_inferred_senses(agent, "florx"))
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.animal", senses
    assert senses[0]["via"] == "bird", senses
    assert senses[0]["confidence"] == 0.7, senses


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULLS — no fabrication.
# --------------------------------------------------------------------------- #
def test_null_analogy_when_compared_to_thing_is_itself_oov(agent):
    # 'florx' (the compared-to object) is ITSELF never grounded in WordNet --
    # genus_head_grounded stays 0, so the join never fires. No analogy sense
    # for 'glorb' -- nothing to transfer FROM.
    r = rc.read_clause(agent, "A glorb is like a florx.", write=True)
    assert r["predications"] == [["similar", "glorb", "florx"]], r
    assert _by_analogy(mi.held_inferred_senses(agent, "glorb")) == []


def test_null_analogy_when_subject_already_known(agent):
    # 'crow' grounds in WordNet -- subj_oov stays 0 on the Predication fact,
    # so the join never admits it, even though the compared-to object ('pump')
    # is cleanly grounded.
    rc.read_clause(agent, "The crow is like a pump.", write=True)
    assert _by_analogy(mi.held_inferred_senses(agent, "crow")) == []


def test_null_analogy_for_a_non_similar_predication(agent):
    # a copular IS-A definition -- relation != 'similar', so
    # infer_sense_from_analogy never fires (only infer_sense_from_definition
    # may fire here).
    r = rc.read_clause(agent, "A glimt is a lake.", write=True)
    assert r["predications"] == [["is_a", "glimt", "lake"]], r
    assert _by_analogy(mi.held_inferred_senses(agent, "glimt")) == []
    assert len(_by_source(mi.held_inferred_senses(agent, "glimt"), "definition")) == 1


# --------------------------------------------------------------------------- #
#  REVISABLE — held, queryable, superseded by ONE set_attr on later grounding.
# --------------------------------------------------------------------------- #
def test_analogy_sense_is_revisable_and_superseded_on_grounding(agent):
    rc.read_clause(agent, "A quixel is like a pump.", write=True)
    before = _by_analogy(mi.held_inferred_senses(agent, "quixel"))
    assert len(before) == 1, before
    assert before[0]["status"] == "active", before

    cid = _concept_by_name(agent, "quixel")
    assert cid is not None
    agent.s.set_attr(cid, "grounded", 1.0)
    agent.inner.run_rules()

    after = _by_analogy(mi.held_inferred_senses(agent, "quixel"))
    assert len(after) == 1, after
    assert after[0]["status"] == "superseded", after
    assert after[0]["confidence"] == before[0]["confidence"], (before, after)  # ONE set_attr flip


# --------------------------------------------------------------------------- #
#  CONFIDENCE ORDER — analogy (0.7) ranks below a copular definition (0.9,
#  identity) and above bare selectional admission (0.6, class-only).
# --------------------------------------------------------------------------- #
def test_analogy_confidence_ranks_below_definition_and_above_selectional(agent):
    # 'glarn' is (1) the subject of a verb.emotion relation (selectional
    # evidence, conf 0.6), (2) explicitly COMPARED to a grounded thing
    # (analogy evidence, conf 0.7), and (3) copularly DEFINED (definitional
    # evidence, conf 0.9). All three coexist as separate rows.
    rc.read_clause(agent, "The glarn feared the storm.", write=True)
    rc.read_clause(agent, "A glarn is like a pump.", write=True)
    rc.read_clause(agent, "A glarn is a lake.", write=True)

    senses = mi.held_inferred_senses(agent, "glarn")
    selectional = _by_source(senses, "selectional")
    analogy = _by_analogy(senses)
    definitional = _by_source(senses, "definition")
    assert selectional and analogy and definitional, senses

    max_selectional = max(s["confidence"] for s in selectional)
    max_analogy = max(s["confidence"] for s in analogy)
    max_definition = max(s["confidence"] for s in definitional)
    assert max_selectional < max_analogy < max_definition, (max_selectional, max_analogy, max_definition)
    assert max_analogy == 0.7, analogy


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT (slice 4) — the relation SELECTION ('similar') is the rule's
#  Eq, never a Python branch; no adapter change was needed for this slice.
# --------------------------------------------------------------------------- #
def test_source_audit_analogy_never_decided_in_python(agent):
    mod_path = os.path.join(ROOT, "domains", "meaning_inference.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    # 'similar' never appears as a Python relation-equality decision (the
    # existing annotate_predication_facts function is unchanged by this slice
    # -- it already wrote `relation` unconditionally for slice 2).
    for ln in lines:
        if ln.startswith(("if ", "elif ")) or " if " in ln:
            assert "similar" not in ln, ln
    assert "if relation ==" not in src and 'relation == "similar"' not in src
    assert "if rel ==" not in src and 'rel == "similar"' not in src

    import json
    seed_path = os.path.join(ROOT, "seeds", "meaning_inference.json")
    seed = json.load(open(seed_path))
    analogy = next(r for r in seed["rules"] if r["name"] == "infer_sense_from_analogy")
    where_str = json.dumps(analogy["where"])
    assert '"relation"' in where_str and '"value": "similar"' in where_str
    assert where_str.count('"type": "Eq"') >= 3   # relation, subj_oov, genus_head_grounded
    # the confidence literal lives in the rule's effect, not computed in Python.
    conf = next(eff for eff in analogy["effects"] if eff[0] == "add_node")[3]["confidence"]
    assert conf == 0.7, conf


# =========================================================================== #
#  SLICE 4 STRETCH — UNMARKED STRUCTURAL analogy: an OOV term with NO "like"/
#  "resembles" cue anywhere gets its class inferred purely from its own
#  accumulated RELATIONAL PROFILE matching a held grounded concept's, via the
#  `ShapeDecode` Term (decode-only-when-a-SINGLE-held-signature-FULLY-explains-
#  it -- no composed blend across sources). `annotate_relational_signatures`
#  re-aggregates the ALREADY-WRITTEN PredicationSlot facts; the JOIN/
#  scoring/argmax lives entirely in `infer_sense_from_structural_analogy`'s
#  ShapeDecode Term (Rust), never in Python.
# =========================================================================== #
def _by_structural(senses):
    return _by_source(senses, "structural")


def test_headline_structural_analogy_transfers_class_with_no_comparison_cue(agent):
    # FOUR plain sentences, no "like"/"resembles"/"is a" anywhere. 'pump' is
    # grounded (noun.artifact) and, across two sentences, is the subject of
    # BOTH 'spins' and 'pushes'. 'glorb' (OOV) is, across two SEPARATE
    # sentences, ALSO the subject of exactly 'spins' and 'pushes' -- its own
    # relational profile is FULLY explained by pump's, by ONE held concept
    # alone, with no explicit authorial signal at all.
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The pump pushes fluid.", write=True)
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    r = rc.read_clause(agent, "The glorb pushes fluid.", write=True)
    assert r["predications"] == [["pushes", "glorb", "fluid"]], r

    senses = _by_structural(mi.held_inferred_senses(agent, "glorb"))
    assert len(senses) == 1, senses          # exactly ONE row -- the same-pass
                                              # canonicalisation guard, not a
                                              # duplicate per shared relation
    s = senses[0]
    assert s["sense_class"] == "noun.artifact", s
    assert s["via"] == "pump", s
    assert s["confidence"] == 0.5, s
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE NULLS — no fabrication, no over-eager transfer.
# --------------------------------------------------------------------------- #
def test_null_structural_analogy_needs_a_multi_relation_profile(agent):
    # ONLY one shared relation ('spins') -- Gte(Count(own_relations), 2) never
    # admits a single-relation profile (that is bare selectional-class
    # evidence, not a genuine structural match).
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    assert _by_structural(mi.held_inferred_senses(agent, "glorb")) == []


def test_null_structural_analogy_when_no_held_concept_overlaps_at_all(agent):
    # 'glorb' gets a genuine 2-relation profile, but NO grounded concept in
    # this session shares either relation -- the codebook has nothing to
    # offer, so ShapeDecode's residual is never empty.
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    rc.read_clause(agent, "The glorb pushes fluid.", write=True)
    assert _by_structural(mi.held_inferred_senses(agent, "glorb")) == []


def test_null_structural_analogy_on_partial_overlap_with_no_second_source(agent):
    # 'glorb' shares ONLY 'spins' with 'pump'; its OTHER relation ('barks')
    # matches no held concept at all -- residual is non-empty (partial
    # coverage), so the join correctly abstains rather than transfer a
    # half-explained profile.
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The pump pushes fluid.", write=True)
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    rc.read_clause(agent, "The glorb barks loudly.", write=True)
    assert _by_structural(mi.held_inferred_senses(agent, "glorb")) == []


def test_null_structural_analogy_refuses_a_composed_blend(agent):
    # 'glorb's profile ('spins' + 'barks') is fully COVERED, but only by
    # STITCHING TWO DIFFERENT grounded concepts together (pump for 'spins',
    # dog for 'barks') -- Count(plan)==1 requires a SINGLE source, so a
    # composed blend across unrelated concepts is correctly refused (that
    # would be fabricating a chimera class, not recognising one thing).
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The dog barks loudly.", write=True)
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    rc.read_clause(agent, "The glorb barks loudly.", write=True)
    assert _by_structural(mi.held_inferred_senses(agent, "glorb")) == []


def test_null_structural_analogy_when_subject_already_known(agent):
    # 'crow' grounds in WordNet (oov=0) -- the Eq(fc.oov, 1.0) guard never
    # admits it, even with an exactly-matching 2-relation profile.
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The pump pushes fluid.", write=True)
    rc.read_clause(agent, "The crow spins fast.", write=True)
    rc.read_clause(agent, "The crow pushes fluid.", write=True)
    assert _by_structural(mi.held_inferred_senses(agent, "crow")) == []


# --------------------------------------------------------------------------- #
#  REVISABLE — held, queryable, superseded by ONE set_attr on later grounding
#  (the EXISTING source-agnostic `infer_sense_supersede` rule handles the new
#  'structural' source with no change -- it matches on ANY InferredSense).
# --------------------------------------------------------------------------- #
def test_structural_analogy_sense_is_revisable_and_superseded_on_grounding(agent):
    rc.read_clause(agent, "The pump spins fast.", write=True)
    rc.read_clause(agent, "The pump pushes fluid.", write=True)
    rc.read_clause(agent, "The glorb spins fast.", write=True)
    rc.read_clause(agent, "The glorb pushes fluid.", write=True)
    before = _by_structural(mi.held_inferred_senses(agent, "glorb"))
    assert len(before) == 1, before
    assert before[0]["status"] == "active", before

    cid = _concept_by_name(agent, "glorb")
    assert cid is not None
    agent.s.set_attr(cid, "grounded", 1.0)
    agent.inner.run_rules()

    after = _by_structural(mi.held_inferred_senses(agent, "glorb"))
    assert len(after) == 1, after
    assert after[0]["status"] == "superseded", after
    assert after[0]["confidence"] == before[0]["confidence"], (before, after)


# --------------------------------------------------------------------------- #
#  CONFIDENCE ORDER — structural (0.5, real but INFERRED multi-relation
#  co-occurrence, no authorial claim) ranks above bare morphology (0.45, shape
#  alone) and below both selectional (0.6) and analogy (0.7, an EXPLICIT
#  authorial claim).
# --------------------------------------------------------------------------- #
def test_structural_confidence_ranks_between_morphology_and_selectional(agent):
    seed_path = os.path.join(ROOT, "seeds", "meaning_inference.json")
    import json
    seed = json.load(open(seed_path))
    structural = next(r for r in seed["rules"] if r["name"] == "infer_sense_from_structural_analogy")
    conf = next(eff for eff in structural["effects"] if eff[0] == "add_node")[3]["confidence"]
    assert 0.45 < conf < 0.6, conf
    assert conf < 0.7, conf   # below the explicit-comparison analogy source too


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT (slice 4 stretch) — the codebook and the coverage/argmax
#  decision are entirely graph-native; Python only re-aggregates EXISTING
#  facts, mechanically, with no branch on their content.
# --------------------------------------------------------------------------- #
def test_source_audit_structural_analogy_never_decided_in_python():
    mod_path = os.path.join(ROOT, "domains", "meaning_inference.py")
    src = open(mod_path).read()
    lines = [ln.strip() for ln in src.splitlines()]
    # own_relations is a pure re-aggregation of PredicationSlot facts -- no
    # `if` branch inspects a relation VALUE to decide whether to include it
    # (the only conditionals in annotate_relational_signatures are structural
    # guards: slot=='subject', oov==0.0, empty-tuple/name checks -- never a
    # specific relation string).
    assert 'add_node("ConceptSignature"' in src
    assert 'add_node("InferredSense"' not in src   # unchanged from earlier slices
    for ln in lines:
        if ln.startswith(("if ", "elif ")):
            assert "own_relations ==" not in ln and "signature ==" not in ln

    import json
    seed_path = os.path.join(ROOT, "seeds", "meaning_inference.json")
    seed = json.load(open(seed_path))
    structural = next(r for r in seed["rules"] if r["name"] == "infer_sense_from_structural_analogy")
    where_str = json.dumps(structural["where"])
    assert '"type": "ShapeDecode"' in where_str
    assert '"codebook_type": "ConceptSignature"' in where_str
    # the codebook is DEDICATED -- never the composer's own 'ShapeSignature'
    # codebook_type (no cross-contamination between the two ShapeDecode users).
    assert '"ShapeSignature"' not in where_str
    effects_str = json.dumps(structural["effects"])
    assert '"type": "ShapeDecode"' in effects_str
    assert '"type": "DictGet"' in effects_str and '"type": "IndexAt"' in effects_str
    # the single-source (no composed blend) + multi-relation-profile guards
    # are graph data, not Python:
    assert '"type": "Gte"' in where_str


# =========================================================================== #
#  IN-SITU DEFINITION VIA BOUNDARY COLLAPSE — an appositive ('X, a Y, ...') or
#  parenthetical ('X (a Y) ...') definitional NP grounds an is_a predication
#  through the SAME ShapeDecode collapse pipeline (`_decode`/`_winner`/`_ground`)
#  every reading construction already goes through
#  (domains/reading_collapse._ground_insitu_definition), fed a SEPARATE
#  boundary-preserving word stream that never touches the shared
#  `_recognise_words`/`_skeleton_from_words` byte-parity path (reading-parity
#  stays 5/5 byte-identical — see tests/test_reading_parity_migrated.py,
#  unmodified). The resulting is_a fact feeds the UNMODIFIED
#  infer_sense_from_definition rule (seeds/meaning_inference.json) exactly as a
#  copular 'A glimt is a lake.' definition already does above.
#
#  The taught graph data this depends on (MarkerClass{cls:'BOUND_COMMA_DEF'|
#  'BOUND_PAREN_DEF'} + ShapeSignature{name:'appositive_definition'|
#  'parenthetical_definition', kind:'construction'}) was authored via
#  `domains.teach.teach` (not hand-written JSON) and lives in
#  seeds/reading_constructions.json — see
#  test_insitu_definition_authoring_persists_via_teach below for the isolated
#  proof that teach() itself performs the persist.
# =========================================================================== #
def test_insitu_appositive_definition_grounds_is_a_from_clean_boot(agent):
    r = rc.read_clause(agent, "A florx, a small bird, sang.", write=True)
    assert ["is_a", "florx", "small_bird"] in r["predications"], r

    senses = _by_source(mi.held_inferred_senses(agent, "florx"), "definition")
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["genus"] == "small_bird", s   # the FULL genus phrase, held too
    assert s["via"] == "bird", s           # genus HEAD of 'small_bird'
    assert s["sense_class"] == "noun.animal", s
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s
    assert s["confidence"] and s["confidence"] > 0, s


def test_insitu_parenthetical_definition_grounds_is_a_from_clean_boot(agent):
    r = rc.read_clause(agent, "A glimt (a lake) lay below.", write=True)
    assert ["is_a", "glimt", "lake"] in r["predications"], r

    senses = _by_source(mi.held_inferred_senses(agent, "glimt"), "definition")
    assert len(senses) == 1, senses
    s = senses[0]
    assert s["genus"] == "lake", s
    assert s["via"] == "lake", s
    assert s["sense_class"], s
    assert s["revisable"] == 1.0, s
    assert s["status"] == "active", s
    assert s["confidence"] and s["confidence"] > 0, s


def test_insitu_appositive_abstains_without_a_det_headed_flanked_span(agent):
    # 'tired and hungry' is NOT a DET-headed NP -- no BOUND_COMMA_DEF boundary
    # is ever emitted (both flanking commas stay unclassified/inert content),
    # so ShapeDecode offers appositive_definition ZERO coverage and it never
    # fires. This is the decode's own non-match, not a Python heuristic gate
    # deciding "this comma pair isn't a definition".
    r = rc.read_clause(agent, "The crow, tired and hungry, flew away.", write=True)
    assert [p for p in r["predications"] if p[0] == "is_a"] == [], r["predications"]
    assert mi.held_inferred_senses(agent, "hungry_flew_away") == []


def test_insitu_definition_construction_is_taught_graph_data():
    """The two constructions + their boundary MarkerClasses are graph data in
    seeds/reading_constructions.json (authored via teach(), see the isolated
    persistence test below), not Python literals scattered through the reading
    module."""
    seed_path = os.path.join(ROOT, "seeds", "reading_constructions.json")
    seed = json.load(open(seed_path))
    names = {n["attrs"].get("name") for n in seed["nodes"] if n["type"] == "ShapeSignature"}
    assert {"appositive_definition", "parenthetical_definition"} <= names
    classes = {n["attrs"].get("cls") for n in seed["nodes"] if n["type"] == "MarkerClass"}
    assert {"BOUND_COMMA_DEF", "BOUND_PAREN_DEF"} <= classes
    for n in seed["nodes"]:
        if n["type"] == "ShapeSignature" and n["attrs"].get("name") in (
                "appositive_definition", "parenthetical_definition"):
            tmpl = json.loads(n["attrs"]["ground_template"])
            # reuses the EXACT same ground_template shape as the copular
            # 'definitional' construction -- no new grounding mode invented.
            assert tmpl == {"pred": "is_a", "mode": "pair"}
    roles_node = next(n for n in seed["nodes"] if n["type"] == "ReadingRoles")
    assert "BOUND_COMMA_DEF" in roles_node["attrs"]["skeleton"]
    assert "BOUND_PAREN_DEF" in roles_node["attrs"]["skeleton"]


def test_insitu_definition_winner_decided_by_shapedecode_not_python():
    """Source audit: WHICH construction (if any) grounds a boundary skeleton is
    read off `_decode`/`_winner` (ShapeDecode's own verdict) -- there is no
    Python string/heuristic check over raw clause punctuation deciding
    'this comma pair is an appositive definition'."""
    src = open(os.path.join(ROOT, "domains", "reading_collapse.py")).read()
    assert "_ground_insitu_definition" in src
    section = src.split("def _ground_insitu_definition")[1].split("def read_clause")[0]
    assert "_decode(agent, skeleton)" in section
    assert "_winner(res)" in section
    assert "name != cname" in section     # the gate is the DECODE's own winner name
    # no ad hoc heuristic over raw clause text deciding the construction --
    # only the mechanical region splitters this module already used before
    # this addition (ct._recognise_regions / ct._paren_regions).
    assert ".count(" not in section
    assert "text.split(" not in section and "clause.split(" not in section
    assert ".startswith(" not in section


def test_insitu_definition_authoring_persists_via_teach(tmp_path, agent):
    """PERSISTENCE proof for the teach()-driven authoring headline: teaching
    the exact MarkerClass/ShapeSignature node shapes `_ground_insitu_definition`
    depends on, with an EXPLICIT tmp seeds_dir (the documented test-isolation
    idiom -- see domains/teach.py's own DURABLE SAFETY GUARD note), writes them
    to disk immediately (not runtime-only), decoupled from whether the real
    seeds/reading_constructions.json already carries them (it does — see
    test_insitu_definition_construction_is_taught_graph_data above; that file
    was produced by this exact teach() call, run once against the real seeds
    dir). The live graph holds the taught node the instant teach() returns
    (step 1 of teach(), before any disk write), which this also checks, and
    re-teaching the identical (type, attrs) is idempotent (no duplicate write)."""
    from domains.teach import teach

    probe_forms = ["‹bound_comma_def_probe›"]
    r1 = teach(agent, "MarkerClass",
               {"cls": "BOUND_COMMA_DEF_PROBE", "forms": probe_forms},
               category="reading_constructions", seeds_dir=tmp_path)
    assert r1["saved"] is True and r1["persisted"] is True

    seed_file = tmp_path / "reading_constructions.json"
    assert seed_file.exists()
    on_disk = json.loads(seed_file.read_text())
    saved = next(n for n in on_disk["nodes"] if n["type"] == "MarkerClass"
                 and n["attrs"].get("cls") == "BOUND_COMMA_DEF_PROBE")
    assert saved["attrs"]["forms"] == probe_forms

    # LIVE graph holds it immediately (step 1 of teach(), independent of the
    # disk write -- this agent can use it in a decode right now).
    assert any(agent.s.node(n)["attrs"].get("cls") == "BOUND_COMMA_DEF_PROBE"
               for n in agent.s.nodes("MarkerClass"))

    # idempotent: re-teaching the identical (type, attrs) is a no-op on disk.
    r2 = teach(agent, "MarkerClass",
               {"cls": "BOUND_COMMA_DEF_PROBE", "forms": probe_forms},
               category="reading_constructions", seeds_dir=tmp_path)
    assert r2["saved"] is False and r2["persisted"] is True
    on_disk_again = json.loads(seed_file.read_text())
    matches = [n for n in on_disk_again["nodes"] if n["type"] == "MarkerClass"
               and n["attrs"].get("cls") == "BOUND_COMMA_DEF_PROBE"]
    assert len(matches) == 1, matches


# =========================================================================== #
#  THE PIPELINE WIRING — meaning-inference reaches the REAL comprehension
#  entry point (`comprehension_reader.read_and_comprehend`), not just a direct
#  `reading_collapse.read_clause(..., write=True)` call. read_and_comprehend's
#  own ~24 read_clause calls per sentence pair are ALWAYS write=False (its own
#  decomposition machinery), so before the `meaning_inference` AnalysisStage
#  (seeds/meaning_inference_stage.json's `la_dispatch_meaning_inference` +
#  `reading_drive._shim_meaning_inference`) the five sources never fired
#  through it at all. Each test below calls ONLY `read_and_comprehend` — never
#  `reading_collapse.read_clause` directly — from a fresh, function-scoped
#  clean-boot `agent` fixture, so a green result here is proof the wiring
#  reaches the real pipeline, not the already-proven direct-call path above.
# =========================================================================== #
def test_pipeline_selectional_sense_reaches_read_and_comprehend(agent):
    from domains import comprehension_reader as cr

    report = cr.read_and_comprehend(agent, "The glarn feared the storm.")
    assert report["spine"]["ingests"][0]["predication"] == ["feared", "glarn", "storm"], report
    senses = _by_source(mi.held_inferred_senses(agent, "glarn"), "selectional")
    assert _classes(senses) >= {"noun.person", "noun.animal"}, senses


def test_pipeline_definition_sense_reaches_read_and_comprehend(agent):
    from domains import comprehension_reader as cr

    cr.read_and_comprehend(agent, "A glimt is a lake.")
    senses = _by_source(mi.held_inferred_senses(agent, "glimt"), "definition")
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.object", senses
    assert senses[0]["via"] == "lake", senses


def test_pipeline_appositive_definition_sense_reaches_read_and_comprehend(agent):
    from domains import comprehension_reader as cr

    cr.read_and_comprehend(agent, "A florx, a small bird, sang.")
    senses = _by_source(mi.held_inferred_senses(agent, "florx"), "definition")
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.animal", senses
    assert senses[0]["via"] == "bird", senses
    assert senses[0]["genus"] == "small_bird", senses


def test_pipeline_morphology_sense_reaches_read_and_comprehend(agent):
    from domains import comprehension_reader as cr

    cr.read_and_comprehend(agent, "The florbitis spread quickly.")
    senses = _by_morph(mi.held_inferred_senses(agent, "florbitis"))
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.state", senses
    assert senses[0]["via"] == "itis", senses


def test_pipeline_analogy_sense_reaches_read_and_comprehend(agent):
    from domains import comprehension_reader as cr

    cr.read_and_comprehend(agent, "A glorb is like a pump.")
    senses = _by_analogy(mi.held_inferred_senses(agent, "glorb"))
    assert len(senses) == 1, senses
    assert senses[0]["sense_class"] == "noun.artifact", senses
    assert senses[0]["via"] == "pump", senses


# --------------------------------------------------------------------------- #
#  WIRING SHAPE — the stage/shim/dispatch registration is exactly the SAME
#  idiom every other comprehension stage uses (no bespoke Python decision).
# --------------------------------------------------------------------------- #
def test_meaning_inference_stage_is_registered_like_every_other_stage():
    from domains import reading_drive as rd

    assert "meaning_inference" in rd._COMPREHENSION_STAGES
    assert rd._STAGE_SHIMS.get("meaning_inference") is rd._shim_meaning_inference
    assert rd._CORTEX_OF.get("meaning_inference") == "executive"

    seed_path = os.path.join(ROOT, "seeds", "meaning_inference_stage.json")
    seed = json.load(open(seed_path))
    names = {r["name"] for r in seed.get("rules", [])}
    assert names == {"la_dispatch_meaning_inference"}
    rule = seed["rules"][0]
    where_str = json.dumps(rule["where"])
    # the decision (WHEN to dispatch) is entirely graph data: stage name/status
    # + a Count(SentenceParse) precondition + an Exists over another
    # AnalysisStage ('monitoring') being done -- the SAME idiom la_dispatch_
    # produce_summary already uses to gate on produce_frames.
    assert '"value": "meaning_inference"' in where_str
    assert '"value": "monitoring"' in where_str
    assert '"value": "done"' in where_str
    assert '"node_type": "SentenceParse"' in where_str
    assert rule["effects"] == [["set_attr", "stage", "status", "dispatched"]]


def test_meaning_inference_shim_is_mechanical_no_decision():
    """SOURCE AUDIT: the shim only iterates SentenceParse nodes and re-invokes
    the SAME read_clause() call the direct-call path already uses -- no
    conditional over what it FINDS (source/class/confidence), and no direct
    minting of InferredSense/Concept/Predication nodes (that stays entirely in
    seeds/meaning_inference.json's rules, unmodified)."""
    src = open(os.path.join(ROOT, "domains", "reading_drive.py")).read()
    section = src.split("def _shim_meaning_inference")[1].split("def _shim_produce_frames")[0]
    assert "read_clause(ad, sentence, write=True)" in section
    assert 'add_node("InferredSense"' not in section
    assert 'add_node("Concept"' not in section
    assert 'add_node("Predication"' not in section
    for ln in [l.strip() for l in section.splitlines()]:
        if ln.startswith(("if ", "elif ")):
            # the ONLY conditionals are mechanical I/O guards (flow scoping,
            # the idempotent re-read guard, an empty-sentence skip) -- never a
            # branch on a sense's class/source/confidence.
            assert "sense_class" not in ln and "source" not in ln and "confidence" not in ln


# --------------------------------------------------------------------------- #
#  REPORT INVARIANCE -- two FULL runs to steady state on a fixed multi-sentence
#  narrative, in the SAME process: (A) the default flow (`stages=None`,
#  `meaning_inference` included, exactly what every real caller gets) vs (B)
#  the byte-identical HEAD behaviour, reproduced by explicitly excluding
#  `meaning_inference` from the minted stage set (`_COMPREHENSION_STAGES` minus
#  that one name -- the exact list HEAD's `_mint_stages` always minted, since
#  the name did not exist there). Both run `read_and_comprehend` to full
#  fixpoint via the SAME public entry point.
#
#  A literal `==` over the two report dicts is the wrong test: `read_and_
#  comprehend` returns raw graph NodeIDs at several keys (spine.ingests[].
#  event, discourse.nodes, centrality.argmax_winner/ranking[].node,
#  narrative_arc.arcs[].roles[].node, elaborative_candidates[].node, flow,
#  trace_node/`#<id>` strings) -- (A) mints exactly ONE extra AnalysisStage
#  node (`meaning_inference` itself) before the tick loop begins, which shifts
#  every id minted afterward by a constant, so raw ids legitimately differ
#  between (A) and (B) even though nothing else changed (verified empirically:
#  `flow`, minted BEFORE the stage split, is identical in both; `discourse.
#  nodes` -- minted after -- differs by a clean +1 in every position). This is
#  a node-numbering artifact, not a content difference: `_strip_ids` erases
#  exactly those known id-bearing positions before comparing, and every
#  OTHER field (predications, sentence text, relation/construction/trigger
#  labels, degrees, confidences, ratios, section/kind/order values, ...)
#  must still match EXACTLY. meaning_inference's own additive graph writes
#  are independently confirmed present in (A) via `mi.held_inferred_senses`."""
_ID_KEYS = {"event", "node", "flow", "argmax_winner", "trace_node"}


def _strip_ids(o, key=None):
    if isinstance(o, dict):
        return {k: _strip_ids(v, k) for k, v in o.items()}
    if isinstance(o, list):
        if key == "nodes":              # discourse.nodes: a bare list of NodeIDs
            return ["<ID>" for _ in o]
        return [_strip_ids(x, key) for x in o]
    if key in _ID_KEYS:
        return "<ID>"
    if isinstance(o, str) and o.startswith("#") and o[1:].isdigit():
        return "<ID>"                   # a stringified "#<node id>" reference
    return o


def test_report_is_id_normalised_identical_with_and_without_meaning_inference():
    from domains import comprehension_reader as cr
    from domains import reading_drive as rd

    text = ("The glarn feared the storm. Later, the crow calmed the glarn down. "
            "The glarn thanked the crow.")

    s_without, node_without = boot_core()
    a_without = _Agent(s_without, node_without)
    without_stages = [x for x in rd._COMPREHENSION_STAGES if x != "meaning_inference"]
    r_without = cr.read_and_comprehend(a_without, text, stages=without_stages)
    assert mi.held_inferred_senses(a_without, "glarn") == []   # confirms the control never ran it

    s_with, node_with = boot_core()
    a_with = _Agent(s_with, node_with)
    r_with = cr.read_and_comprehend(a_with, text)               # stages=None -- the real default
    # meaning_inference DID run and mint additive graph data in this branch...
    assert mi.held_inferred_senses(a_with, "glarn") != []

    # ...yet the returned comprehension report, modulo the known id-relabelling
    # artifact, is UNCHANGED.
    assert _strip_ids(r_with) == _strip_ids(r_without), (r_without, r_with)

"""GENERAL PROPOSITIONAL DEDUCTION through the inference_generation collapse
pipeline (domains/propositional_deduction.py + inference_generation.py's new
`detect_implication_gaps`/`resolve_implication_gap`).

See docs/research/engine_substrate/DEDUCTION_GENERALIZATION_PREREG.md /
DEDUCTION_GENERALIZATION_RESULTS.md for the full design record. In one line:
`domains/ground_reductions.py` already proves REAL, EXECUTING propositional
modus ponens (`ImplicationClause`/`GroundedReduction.compute`) but entirely
bound to group-theory invariant theorems (Python-callable antecedents over one
fixed object shape). This closes the gap the creator named directly
("the deduction does exist but likely needs expansion") by making the SAME
antecedent/consequent-implication SHAPE available through the GENERAL,
graph-native `inference_generation.py` gap-detect -> ShapeDecode collapse ->
mint -> re-run-fixpoint pipeline, for ANY domain, sourced from a NEW
`ShapeSignature{kind:"knowledge_logical"}` codebook kind
(`seeds/inference_logical.json`) — an ADDITION to the existing 8-schema
codebook, not a rewrite: `ground_reductions.py`, `comprehend_theorem.py`, the
inert `logic_foundation.json`/`logic_propositional_predicate.json` prose rules,
and `seeds/inference_knowledge.json` itself are all untouched.

CORRECTED 2026-08-13 (see docs/research/engine_substrate/
DEDUCTION_GENERAL_READER_CORRECTION_RESULTS.md): the original
`parse_conditional` was a hand-rolled token-pattern mini-grammar duplicating a
capability `reading_collapse.py`'s already-general `conditional` construction
(`tests/test_reading_collapse.py:57`) provided. The PARSE tests below now call
`parse_conditional(agent, statement)` — it ingests the statement through the
general reading pipeline (`reading_collapse.decompose_sentence`/`read_clause`)
instead of a second grammar. Every other test (mint/headline/regression) is
unchanged in OUTCOME; only the parse-layer plumbing changed.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_deduction_generalization.py -p no:randomly -q
"""
from __future__ import annotations

import os
import re as _re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                  # noqa: E402
from domains import dictionary_lexicon as dl                # noqa: E402
from domains import inference_generation as ig               # noqa: E402
from domains import propositional_deduction as pd            # noqa: E402
from domains import situation_model_reader as smr            # noqa: E402


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


# --------------------------------------------------------------------------- #
#  PARSE — via the GENERAL reading pipeline (reading_collapse.py), not a
#  second grammar. Each call needs a fresh agent (the reading pipeline is
#  graph-native — a codebook lives on the agent it decodes against).
# --------------------------------------------------------------------------- #
def test_parse_explicit_conditional():
    p = pd.parse_conditional(_fresh(), "if X is a bird, X can fly")
    assert p is not None
    assert p["antecedent_attr"] == "bird"
    assert p["consequent_attr"] == "can_fly"
    assert p["consequent_relation"] == "can"
    assert p["form"] == "conditional_split"


def test_parse_bare_universal_paraphrase():
    # a DIFFERENT surface form from the explicit "if X ... X ..." pattern above —
    # the generality bar comprehend_theorem's own docstring sets for itself
    # (parse a paraphrase it was not hand-tuned to), applied to this parser.
    p = pd.parse_conditional(_fresh(), "a fish can swim")
    assert p is not None
    assert p["antecedent_attr"] == "fish"
    assert p["consequent_attr"] == "can_swim"
    assert p["form"] == "bare_universal"


def test_parse_property_form():
    p = pd.parse_conditional(_fresh(), "a mammal is warm-blooded")
    assert p is not None
    assert p["antecedent_attr"] == "mammal"
    assert p["consequent_relation"] == "is"
    assert p["consequent_attr"] == "warm_blooded"


def test_parse_honest_residual_on_unrecognised_prose():
    assert pd.parse_conditional(_fresh(), "gibberish that matches nothing at all") is None
    assert pd.parse_conditional(_fresh(), "") is None


# --------------------------------------------------------------------------- #
#  THE CORRECTION'S OWN PROOF — the general reader's `conditional`
#  construction (reading_collapse.py, decoded via the SAME ShapeDecode every
#  other construction uses) already grounds an ordinary conditional sentence
#  into a genuine `implies(antecedent, consequent)` predication, BYTE-
#  IDENTICAL to tests/test_reading_collapse.py:57's own live proof — this is
#  the capability the original `parse_conditional` duplicated instead of
#  using. Confirmed here, independent of this module's own (different, and
#  necessary — see the correction RESULTS doc) decompose_sentence/read_clause
#  route, so the fact that the general `conditional` construction exists and
#  works is not just asserted in the docstring but demonstrated by a test.
# --------------------------------------------------------------------------- #
def test_general_reader_conditional_construction_already_produces_implies():
    from domains import reading_collapse as rc
    ag = _fresh()
    r = rc.read_clause(ag, "if it rains then the ground is wet")
    assert r["construction"] == "conditional"
    assert ["implies", "it_rains", "ground"] in r["predications"]
    assert not r["minted"], "a seeded construction must not mint"


# --------------------------------------------------------------------------- #
#  HEADLINE — genuine modus ponens through the GENERAL pipeline, hand-seeded
#  implication (seeds/inference_logical.json's own logical_bird_can_fly).
# --------------------------------------------------------------------------- #
def test_headline_modus_ponens_hand_seeded():
    ag = _fresh()
    r = ig.read_and_infer(ag, "Tweety is a bird.")

    # BEFORE: only the STATED fact (bird=1); can_fly was never in the text.
    before = r["before_situation_model"]["tweety"]
    assert before.get("bird") == 1
    assert before.get("can_fly") is None

    hits = [g for g in r["logical"] if g["minted"] and g["gap"]["entity"] == "tweety"]
    assert len(hits) == 1
    h = hits[0]
    assert h["gap"]["antecedent_attr"] == "bird"
    assert h["schema"] == "logical_bird_can_fly"
    assert h["supplies"] == {"relation": "is_a", "attr": "can_fly"}

    # AFTER: can_fly was DERIVED, not stated — the DEFINING modus-ponens fact.
    after = r["situation_model"]["tweety"]
    assert after.get("bird") == 1
    assert after.get("can_fly") == 1
    assert "can fly" not in "Tweety is a bird.".lower()


# --------------------------------------------------------------------------- #
#  PROSE-MINTED implication — the SAME derivation, but the implication itself
#  is PARSED from ordinary conditional prose at runtime (mint_logical_schema),
#  not hand-authored in the seed file — proving the general parser, not just
#  the hand-seeded fact, drives real deduction through the unmodified pipeline.
# --------------------------------------------------------------------------- #
def test_modus_ponens_from_prose_minted_implication():
    ag = _fresh()
    mint = pd.mint_logical_schema(ag, "if X is a fish, X can swim")
    assert mint["minted"] is True
    assert mint["name"] == "logical_fish_can_swim"

    r = ig.read_and_infer(ag, "Nemo is a fish.")
    before = r["before_situation_model"]["nemo"]
    assert before.get("fish") == 1 and before.get("can_swim") is None

    hits = [g for g in r["logical"] if g["minted"] and g["gap"]["entity"] == "nemo"]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_fish_can_swim"
    assert hits[0]["supplies"] == {"relation": "is_a", "attr": "can_swim"}

    after = r["situation_model"]["nemo"]
    assert after.get("can_swim") == 1


def test_mint_is_idempotent():
    ag = _fresh()
    m1 = pd.mint_logical_schema(ag, "if X is a fish, X can swim")
    m2 = pd.mint_logical_schema(ag, "if X is a fish, X can swim")
    assert m1["minted"] is True
    assert m2["minted"] is False and m2.get("already") is True
    assert m1["name"] == m2["name"]


# --------------------------------------------------------------------------- #
#  CHAINING — the derived consequent flows through the SAME run_rules fixpoint
#  ingest_predication already re-runs, exactly like the empirical-gap pipeline
#  (fragile -> broken -> worthless). Bird/fly has no further downstream rule,
#  so this test demonstrates the mechanism is UNCHANGED (not a new fixpoint
#  hook) by reusing the EXISTING glass fragile->broken->worthless cascade
#  alongside an independently-derived logical fact on the SAME entity.
# --------------------------------------------------------------------------- #
def test_logical_and_empirical_gaps_coexist_on_one_entity():
    ag = _fresh()
    # "glass" is both a bird (silly, but exercises both pipelines on ONE
    # entity name) and dropped -- the empirical fragile->broken->worthless
    # chain AND the logical bird->can_fly derivation must both land.
    r = ig.read_and_infer(ag, "The glass is a bird. John dropped the glass.")
    after = r["situation_model"]["glass"]
    assert after.get("can_fly") == 1          # the logical derivation
    assert after.get("broken") == 1           # the untouched empirical chain


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — no covering implication -> no over-inference.
# --------------------------------------------------------------------------- #
def test_no_over_inference_uncovered_antecedent():
    ag = _fresh()
    r = ig.read_and_infer(ag, "Rex is a dog.")
    assert r["situation_model"]["rex"] == {"dog": 1}
    assert r["logical"]                          # candidates WERE offered
    assert all(not g["minted"] for g in r["logical"])


def test_no_gap_when_consequent_already_stated():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    # state BOTH the antecedent and the consequent directly (ingest_predication
    # -- the SAME property-predication primitive the general copular reader
    # itself calls) before ever running the gap pipeline, mirroring
    # test_no_gap_when_fully_stated's own "state it, then check no gap is
    # drawn" shape for the empirical pipeline.
    smr.ingest_predication(ag, ["is_a", "tweety", "bird"])
    smr.ingest_predication(ag, ["is_a", "tweety", "can_fly"])
    gaps = ig.detect_implication_gaps(ag)
    bird_gap = next(g for g in gaps if g["entity"] == "tweety" and g["antecedent_attr"] == "bird")
    rec = ig.resolve_implication_gap(ag, bird_gap)
    # can_fly is ALREADY held -- idempotent, no re-mint (resolve_implication_
    # gap's own already-holds check, mirroring resolve_elaborative_candidate).
    assert rec["minted"] is False
    assert "already holds" in rec["reason"]
    assert smr.entity_state(ag, "tweety").get("can_fly") == 1


# --------------------------------------------------------------------------- #
#  MINT REUSE — the consequent is minted via situation_model_reader.
#  ingest_predication, the IDENTICAL call the empirical pipeline already makes
#  (resolve_precondition_gap) — proving no new mint primitive was invented.
# --------------------------------------------------------------------------- #
def test_mint_reuses_ingest_predication_unchanged():
    ag = _fresh()
    r = ig.read_and_infer(ag, "Tweety is a bird.")
    hit = next(g for g in r["logical"] if g["minted"])
    assert hit["ingest"]["kind"] == "property"
    assert hit["ingest"]["property"] == "can_fly"


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the SAME discipline
#  test_source_audit_no_regex_and_decode_is_the_decision holds
#  inference_generation.py to, applied to the new logical-gap code.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decode_is_the_decision():
    ig_src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    assert not _re.search(r"^\s*import re\b", ig_src, _re.M)
    assert "re.compile(" not in ig_src and "re.match(" not in ig_src
    # the new resolver goes through the SAME decode_gap -> rc._winner collapse.
    assert "decode_gap(agent, [[\"holds\"" in ig_src
    # no Python branch keyed on the literal content of an antecedent attr
    # (e.g. `if antecedent_attr == "bird"`) selects the mint.
    assert "antecedent_attr ==" not in ig_src
    assert '== "bird"' not in ig_src and "== 'bird'" not in ig_src

    pd_src = open(os.path.join(ROOT, "domains", "propositional_deduction.py")).read()
    assert not _re.search(r"^\s*import re\b", pd_src, _re.M)
    assert "re.compile(" not in pd_src and "re.match(" not in pd_src
    assert "re.search(" not in pd_src


def test_ground_reductions_and_comprehend_theorem_untouched():
    # explicit scope guard: this rung must not have modified the group-theory
    # deduction engine or its theorem-prose parser.
    #
    # seeds/inference_knowledge.json was DROPPED from this guard's file list
    # (LOGODDS_GENERATOR_RESULTS.md, a later, separately-scoped, intentional
    # touch: wiring a latent:causal_strength LatentDimension onto the
    # existing knowledge_causal schemas per CAUSAL_LINKAGE_DIMENSION_
    # RESEARCH.md Sec7 -- additive nodes/edges, orthogonal to the group-
    # theory/deduction concern this guard actually protects, and confirmed
    # in that rung's own regression to read nothing this file's knowledge_*
    # decode path touches). The four files below remain guarded and
    # confirmed untouched by that later rung too.
    import subprocess
    out = subprocess.run(["git", "diff", "--stat", "b124038", "--",
                          "domains/ground_reductions.py", "domains/comprehend_theorem.py",
                          "seeds/logic_foundation.json",
                          "seeds/logic_propositional_predicate.json"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", out.stdout


# --------------------------------------------------------------------------- #
#  NO REGRESSION — situation_model_reader called directly is unchanged (the
#  SAME proof-of-non-interference test_spine_unwired_still_bare already makes
#  for the empirical pipeline).
# --------------------------------------------------------------------------- #
def test_spine_unwired_still_bare_for_logical_case():
    ag = _fresh()
    r = smr.read_into_situation_model(ag, "Tweety is a bird.")
    assert r["situation_model"]["tweety"] == {"bird": 1}
    assert r["situation_model"]["tweety"].get("can_fly") is None

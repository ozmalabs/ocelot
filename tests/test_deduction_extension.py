"""DEDUCTION EXTENSION — modus tollens + conjunctive antecedents, extending
the WORKING facility landed earlier the same day
(`domains/propositional_deduction.py` + `domains/inference_generation.py`'s
`detect_implication_gaps`/`resolve_implication_gap`).

See docs/research/engine_substrate/DEDUCTION_EXTENSION_PREREG.md /
DEDUCTION_EXTENSION_RESULTS.md for the full design record. In one line:

  1. MODUS TOLLENS is graph DATA, not new decode/resolve code:
     `propositional_deduction.derive_contrapositive`/`ensure_contrapositives`
     mechanically installs the contrapositive companion of every held
     `knowledge_logical` schema (P=>Q entails ~Q=>~P), and the EXISTING,
     UNCHANGED `detect_implication_gaps`/`resolve_implication_gap`/
     `decode_gap` run it with zero new gap-detection code.
  2. CONJUNCTIVE ANTECEDENTS ("if X is wet and X is cold, X is frozen") are
     real, new, small machinery: `detect_conjunctive_gaps`/
     `resolve_conjunctive_gap` (new functions), using a DISTINCT relation
     label (`holds_all`, not `holds`) so they can never cross-contaminate
     the existing `holds`-keyed MP/MT pipeline (a genuine false-positive
     risk measured live and closed — see the RESULTS doc Sec3), plus a
     FULL-COVERAGE gate `ShapeDecode`'s own `Covers` matcher does not
     provide on its own (it accepts partial coverage as a valid match).
  3. Quantifiers were investigated as a stretch goal and NOT built — see
     the RESULTS doc Sec4 for the precise finding.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_deduction_extension.py -p no:randomly -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                    # noqa: E402
from domains import dictionary_lexicon as dl                  # noqa: E402
from domains import inference_generation as ig                # noqa: E402
from domains import propositional_deduction as pd             # noqa: E402
from domains import situation_model_reader as smr             # noqa: E402

_BASE = "8af4fde"   # main tip this worktree was cut from


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
#  MODUS TOLLENS — the contrapositive is auto-derived, seed-loaded schemas.
# --------------------------------------------------------------------------- #
def test_contrapositive_auto_derived_for_seed_schemas():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    sub, _, _ = ig._resolve(ag)
    names = {sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")
             if sub.node(n)["attrs"].get("kind") == "knowledge_logical"}
    assert "logical_bird_can_fly_contrapositive" in names
    assert "logical_rain_wet_contrapositive" in names
    # capability form: can_fly negates to not_fly (the bare verb, matching
    # what the general reader's event-construction actually produces for
    # "cannot fly" -- not the literal "not_can_fly").
    cp = pd._schema_by_name(sub, "logical_bird_can_fly_contrapositive")
    assert json.loads(sub.node(cp)["attrs"]["signature"]) == [["holds", "not_fly"]]
    assert json.loads(sub.node(cp)["attrs"]["supplies"]) == {"relation": "is_a", "attr": "not_bird"}
    # property form: wet negates to not_wet directly.
    cp2 = pd._schema_by_name(sub, "logical_rain_wet_contrapositive")
    assert json.loads(sub.node(cp2)["attrs"]["signature"]) == [["holds", "not_wet"]]
    assert json.loads(sub.node(cp2)["attrs"]["supplies"]) == {"relation": "is_a", "attr": "not_rain"}


def test_contrapositive_auto_derived_for_prose_minted_schema():
    ag = _fresh()
    mint = pd.mint_logical_schema(ag, "if X is a fish, X can swim")
    assert mint["minted"] is True
    sub, _, _ = ig._resolve(ag)
    cp = pd._schema_by_name(sub, "logical_fish_can_swim_contrapositive")
    assert cp is not None
    assert json.loads(sub.node(cp)["attrs"]["signature"]) == [["holds", "not_swim"]]
    assert json.loads(sub.node(cp)["attrs"]["supplies"]) == {"relation": "is_a", "attr": "not_fish"}


def test_contrapositive_not_derived_for_conjunctive_schema():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    sub, _, _ = ig._resolve(ag)
    assert pd._schema_by_name(sub, "logical_wet_cold_frozen_contrapositive") is None
    res = pd.derive_contrapositive(ag, "logical_wet_cold_frozen")
    assert res["derived"] is False
    assert "not the single-antecedent" in res["reason"]


def test_contrapositive_not_re_derived_from_a_contrapositive():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    res = pd.derive_contrapositive(ag, "logical_rain_wet_contrapositive")
    assert res["derived"] is False
    assert "itself a derived contrapositive" in res["reason"]


def test_ensure_contrapositives_is_idempotent():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    sub, _, _ = ig._resolve(ag)
    before = sorted(sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")
                     if sub.node(n)["attrs"].get("kind") == "knowledge_logical")
    ig.ensure_logical_seeds(ag)   # re-run (mirrors real resumed-daemon reload)
    after = sorted(sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")
                   if sub.node(n)["attrs"].get("kind") == "knowledge_logical")
    assert before == after


# --------------------------------------------------------------------------- #
#  MODUS TOLLENS — HEADLINE live text demo, matching the task's own literal
#  example exactly: held "if it rains then the ground is wet" + stated
#  "the ground is NOT wet" -> derives the negated antecedent fact.
# --------------------------------------------------------------------------- #
def test_headline_modus_tollens_live_text():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The ground is not wet.")

    before = r["before_situation_model"]["ground"]
    assert before.get("not_wet") == 1
    assert before.get("not_rain") is None

    hits = [g for g in r["logical"] if g["minted"] and g["gap"]["entity"] == "ground"]
    assert len(hits) == 1
    h = hits[0]
    assert h["gap"]["antecedent_attr"] == "not_wet"
    assert h["schema"] == "logical_rain_wet_contrapositive"
    assert h["supplies"] == {"relation": "is_a", "attr": "not_rain"}

    after = r["situation_model"]["ground"]
    assert after.get("not_wet") == 1
    assert after.get("not_rain") == 1          # DERIVED -- "it did not rain"
    assert "rain" not in "The ground is not wet.".lower()


def test_no_false_modus_tollens_when_positive_antecedent_stated():
    """Confirm this does NOT fire when only the POSITIVE antecedent is
    stated -- no false modus-tollens firing on a case that should use
    modus ponens instead. Direct ingest (not raw text) sidesteps the
    unrelated pronoun-grounding question and isolates exactly the fact
    this test is about."""
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    smr.ingest_predication(ag, ["is_a", "ground", "rain"])
    gaps = ig.detect_implication_gaps(ag)
    resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]
    hits = [r for r in resolved if r["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_rain_wet"          # MP fired
    assert hits[0]["supplies"] == {"relation": "is_a", "attr": "wet"}
    state = smr.entity_state(ag, "ground")
    assert state.get("wet") == 1
    assert state.get("not_rain") is None                    # MT did NOT fire
    assert state.get("not_wet") is None


def test_modus_tollens_capability_form_graph_level():
    """The CAPABILITY-consequent contrapositive (bird/can_fly), proven at
    the graph-data level via direct ingest_predication rather than raw text:
    `situation_model_reader._is_property_pred` (situation_model_reader.py)
    only treats is_a/is/cop/designate as property-setting relations, so a
    `can`-relation predication -- positive OR negated -- does not set an
    attr via ordinary TEXT ingestion at all; this is a pre-existing,
    unrelated gap (the original modus-ponens landing never round-tripped a
    capability consequent through raw text either), not something this
    rung fixes or is blocked by. The mechanism itself is proven correct
    here directly."""
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    # "Rex cannot fly" as the general reader actually grounds it
    # (can(rex, not_fly) -- measured live, DEDUCTION_EXTENSION_PREREG.md
    # Sec1), fed directly as the property-predication form this module's
    # schemas expect.
    smr.ingest_predication(ag, ["is_a", "rex", "not_fly"])
    gaps = ig.detect_implication_gaps(ag)
    resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]
    hits = [r for r in resolved if r["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_bird_can_fly_contrapositive"
    assert hits[0]["supplies"] == {"relation": "is_a", "attr": "not_bird"}
    assert smr.entity_state(ag, "rex").get("not_bird") == 1


# --------------------------------------------------------------------------- #
#  CONJUNCTIVE ANTECEDENTS — the partial-match null and the joint-fact mint.
# --------------------------------------------------------------------------- #
def test_conjunction_partial_match_is_a_genuine_null():
    ag = _fresh()
    smr.ingest_predication(ag, ["is_a", "puddle", "wet"])
    gaps = ig.detect_conjunctive_gaps(ag)
    assert gaps and gaps[0]["antecedent_attrs"] == ["wet"]
    resolved = [ig.resolve_conjunctive_gap(ag, g) for g in gaps]
    assert all(not r["minted"] for r in resolved)
    hit = next(r for r in resolved if r.get("schema") == "logical_wet_cold_frozen")
    assert "PARTIAL MATCH" in hit["reason"]
    assert smr.entity_state(ag, "puddle") == {"wet": 1}


def test_conjunction_fires_only_when_both_conjuncts_stated():
    ag = _fresh()
    smr.ingest_predication(ag, ["is_a", "puddle", "wet"])
    smr.ingest_predication(ag, ["is_a", "puddle", "cold"])
    gaps = ig.detect_conjunctive_gaps(ag)
    resolved = [ig.resolve_conjunctive_gap(ag, g) for g in gaps]
    hits = [r for r in resolved if r["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_wet_cold_frozen"
    assert hits[0]["supplies"] == {"relation": "is_a", "attr": "frozen"}
    assert smr.entity_state(ag, "puddle") == {"wet": 1, "cold": 1, "frozen": 1}


def test_conjunction_no_cross_contamination_with_mp_path():
    """THE bug found and fixed while building this (DEDUCTION_EXTENSION_
    RESULTS.md Sec3): merely ADDING a 2-conjunct schema to the SAME
    codebook pool made the EXISTING, unchanged detect_implication_gaps/
    resolve_implication_gap ALSO a candidate decoder for it (ShapeDecode's
    Covers matcher accepts partial coverage). Fixed via a distinct relation
    label (`holds_all`, not `holds`) in the conjunctive schema's own
    `signature` -- this test is the regression guard for that fix: the OLD
    MP pipeline must still return the honest null on 'wet' alone, never
    'frozen'."""
    ag = _fresh()
    smr.ingest_predication(ag, ["is_a", "puddle", "wet"])
    gaps = ig.detect_implication_gaps(ag)
    resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]
    assert all(not r["minted"] for r in resolved)
    assert smr.entity_state(ag, "puddle") == {"wet": 1}


def test_conjunction_end_to_end_live_text():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The puddle is wet. The puddle is cold.")
    before = r["before_situation_model"]["puddle"]
    assert before == {"wet": 1, "cold": 1}
    hits = [g for g in r["conjunctive"] if g["minted"] and g["gap"]["entity"] == "puddle"]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_wet_cold_frozen"
    after = r["situation_model"]["puddle"]
    assert after.get("frozen") == 1
    assert not any(g["minted"] for g in r["logical"] if g["gap"]["entity"] == "puddle")


def test_conjunction_end_to_end_live_text_partial_is_null():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The puddle is wet.")
    assert r["situation_model"]["puddle"] == {"wet": 1}
    assert not any(g["minted"] for g in r["conjunctive"])
    assert not any(g["minted"] for g in r["logical"])


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT + SCOPE GUARDS.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decode_is_the_decision():
    ig_src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    assert not __import__("re").search(r"^\s*import re\b", ig_src, __import__("re").M)
    assert "re.compile(" not in ig_src and "re.match(" not in ig_src
    assert "[\"holds_all\", a] for a in gap[\"antecedent_attrs\"]" in ig_src
    assert "antecedent_attrs ==" not in ig_src

    pd_src = open(os.path.join(ROOT, "domains", "propositional_deduction.py")).read()
    assert not __import__("re").search(r"^\s*import re\b", pd_src, __import__("re").M)
    assert "re.compile(" not in pd_src and "re.match(" not in pd_src


def test_existing_mp_gap_functions_are_byte_unchanged_since_this_mornings_landing():
    """`detect_implication_gaps`/`resolve_implication_gap` must carry ZERO
    trace of this rung's own additions (no `holds_all`, no full-coverage
    `covered_count` gate) -- proving the MT extension is pure DATA and the
    conjunction extension is a genuinely SEPARATE code path, not a rewrite
    of the existing one."""
    ig_src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    start = ig_src.index("def detect_implication_gaps")
    end = ig_src.index("def resolve_implication_gap")
    body1 = ig_src[start:end]
    start2 = ig_src.index("def resolve_implication_gap")
    end2 = ig_src.index("\n\n\n", start2)
    body2 = ig_src[start2:end2]
    assert "holds_all" not in body1 and "holds_all" not in body2
    assert "covered_count" not in body1 and "covered_count" not in body2
    assert "antecedent_attrs" not in body1 and "antecedent_attrs" not in body2


def test_ground_reductions_comprehend_theorem_and_original_seed_files_untouched():
    out = subprocess.run(["git", "diff", "--stat", _BASE, "--",
                          "domains/ground_reductions.py", "domains/comprehend_theorem.py",
                          "seeds/logic_foundation.json",
                          "seeds/logic_propositional_predicate.json",
                          "seeds/inference_knowledge.json"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", out.stdout


def test_deduction_generalization_module_test_file_untouched():
    """This rung must not have edited THIS MORNING's own new test file --
    any new coverage belongs in THIS file."""
    out = subprocess.run(["git", "diff", "--stat", _BASE, "--",
                          "tests/test_deduction_generalization.py"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", out.stdout


# --------------------------------------------------------------------------- #
#  QUANTIFIERS — stretch goal, NOT built. This is a documentation-level
#  confirmation of the investigated finding (not a build), so a future rung
#  that revisits this doesn't have to re-derive it: quantifier WORDS are
#  seeded as plain `determiner`-role ClosedClass members (the SAME role
#  "a"/"the" occupy — `_DETERMINERS`, populated from
#  `seeds/reading_constructions.json`'s own `ClosedClass{role:"determiner"}`
#  data at `ensure_codebook` time), and no construction anywhere in
#  `seeds/reading_constructions.json` names a distinct quantifier-SCOPE
#  relation (no `forall`/`exists`/`scope` predication exists in that
#  codebook) — i.e. there is no bound-variable premise representation for
#  "every"/"some" to ground into today, confirmed by direct read, not
#  assumed. (Separately, and NOT chased further here as it is orthogonal to
#  the quantifier-representation question: the graph-resident `MarkerClass`
#  lexicon `_marker_lexicon` reads for skeleton-marker BUILDING does not
#  list "every" as a DET member the way it lists "a" -- a real, narrow,
#  pre-existing inconsistency between the `ClosedClass` and `MarkerClass`
#  representations, found while investigating this, reported here rather
#  than silently glossed over, and out of this rung's scope to fix.)
# --------------------------------------------------------------------------- #
def test_quantifier_words_are_seeded_determiners_with_no_scope_construction():
    from domains import reading_collapse as rc
    ag = _fresh()
    rc.ensure_codebook(ag)
    # "every"/"some"/"any"/"each" load into the SAME determiner ClosedClass
    # role "a"/"the" occupy, once the codebook is loaded from seed data.
    assert {"every", "some", "any", "each", "a", "the"} <= rc._DETERMINERS
    # no construction in the codebook names a quantifier-SCOPE relation.
    seed_path = os.path.join(ROOT, "seeds", "reading_constructions.json")
    manifest = json.load(open(seed_path))
    predications = {n["attrs"].get("predication") for n in manifest["nodes"]
                    if n.get("type") == "ShapeSignature" and n["attrs"].get("predication")}
    assert not (predications & {"forall", "exists", "scope", "quantify"})

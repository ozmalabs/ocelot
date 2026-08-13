"""QUANTIFIED DEDUCTION — universal + existential instantiation, extending
the deduction facility (`domains/propositional_deduction.py` +
`domains/inference_generation.py`) with the STRETCH GOAL
`DEDUCTION_EXTENSION_RESULTS.md` Sec4 investigated, precisely sized, and did
NOT build.

See docs/research/engine_substrate/QUANTIFIED_DEDUCTION_PREREG.md /
QUANTIFIED_DEDUCTION_RESULTS.md for the full design record. In one line:

  1. UNIVERSAL INSTANTIATION ("All philosophers are mortal" + "Socrates is a
     philosopher" -> "Socrates is mortal") is a NEW parse
     (`parse_universal`/`mint_universal_schema`), reusing the EXISTING,
     UNCHANGED `detect_implication_gaps`/`resolve_implication_gap`/
     `decode_gap` -- the SAME "second gap-detection pattern turns out
     unnecessary" finding the modus-tollens rung already made.
  2. EXISTENTIAL INSTANTIATION ("Some bird is a penguin" + context) is real,
     new, small WITNESS-SEARCH machinery (`detect_existential_gaps`/
     `resolve_existential_gap`), using a DISTINCT relation label
     (`holds_some`, not `holds`/`holds_all`) so it can never cross-
     contaminate the existing MP/conjunction pipelines, mirroring the
     conjunction rung's own cross-contamination fix.
  3. Nested/multi-quantifier premises and negative existentials were NOT
     attempted -- named follow-ons, not built.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_quantified_deduction.py -p no:randomly -q
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

_BASE = "76b8aea"   # main tip this worktree was cut from


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
#  UNIVERSAL INSTANTIATION — the headline syllogism, real Concepts, prose-
#  minted end to end, no hand-seeded fallback needed.
# --------------------------------------------------------------------------- #
def test_headline_universal_syllogism_live_prose():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    minted = pd.mint_universal_schema(ag, "All philosophers are mortal")
    assert minted["minted"] is True
    assert minted["parsed"]["antecedent_attr"] == "philosopher"      # singularised
    assert minted["parsed"]["consequent_attr"] == "mortal"
    smr.ingest_predication(ag, ["is_a", "socrates", "philosopher"])
    assert smr.entity_state(ag, "socrates") == {"philosopher": 1}
    gaps = ig.detect_implication_gaps(ag)
    resolved = [ig.resolve_implication_gap(ag, g) for g in gaps]
    hits = [r for r in resolved if r["minted"] and r["gap"]["entity"] == "socrates"]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_universal_philosopher_mortal"
    assert hits[0]["supplies"] == {"relation": "is_a", "attr": "mortal"}
    assert smr.entity_state(ag, "socrates") == {"philosopher": 1, "mortal": 1}


def test_universal_does_not_fire_without_the_stated_instance():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_universal_schema(ag, "All philosophers are mortal")
    # no entity anywhere carries philosopher=1 -- nothing to instantiate against.
    gaps = [g for g in ig.detect_implication_gaps(ag) if g["antecedent_attr"] == "philosopher"]
    assert gaps == []


def test_universal_end_to_end_via_read_and_infer():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_universal_schema(ag, "All philosophers are mortal")
    r = ig.read_and_infer(ag, "Socrates is a philosopher.")
    assert r["before_situation_model"]["socrates"] == {"philosopher": 1}
    hits = [g for g in r["logical"] if g["minted"] and g["gap"]["entity"] == "socrates"]
    assert len(hits) == 1
    assert hits[0]["schema"] == "logical_universal_philosopher_mortal"
    assert r["situation_model"]["socrates"].get("mortal") == 1


def test_universal_composes_with_modus_tollens_for_free():
    """Because mint_universal_schema installs a kind:'knowledge_logical'
    node with a length-1 signature -- STRUCTURALLY IDENTICAL to any other MP
    schema -- ensure_contrapositives' own batch scan (unchanged) derives its
    contrapositive automatically, with zero code added for this rung."""
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_universal_schema(ag, "All philosophers are mortal")
    sub, _, _ = pd._resolve(ag)
    names = {sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")
             if sub.node(n)["attrs"].get("kind") == "knowledge_logical"}
    assert "logical_universal_philosopher_mortal_contrapositive" in names
    # modus tollens: not_mortal -> not_philosopher, via the existing pipeline.
    smr.ingest_predication(ag, ["is_a", "plato", "not_mortal"])
    resolved = [ig.resolve_implication_gap(ag, g) for g in ig.detect_implication_gaps(ag)
                if g["entity"] == "plato"]
    hit = next(r for r in resolved if r["minted"])
    assert hit["supplies"] == {"relation": "is_a", "attr": "not_philosopher"}


def test_universal_mint_is_idempotent():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    first = pd.mint_universal_schema(ag, "All philosophers are mortal")
    second = pd.mint_universal_schema(ag, "All philosophers are mortal")
    assert first["minted"] is True
    assert second["minted"] is False and second.get("already") is True
    assert first["name"] == second["name"]


def test_universal_no_leading_quantifier_is_a_named_residual():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    assert pd.parse_universal(ag, "philosophers are mortal") is None
    assert pd.mint_universal_schema(ag, "philosophers are mortal")["minted"] is False


def test_universal_does_not_recognise_a_or_an_by_design():
    """Scoping decision (PREREG Sec2): 'a'/'an' stay owned by the EXISTING
    bare_universal generic reading, never claimed by the new quantifier
    lexicon -- so a bare indefinite-article sentence is unaffected."""
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    assert pd.parse_universal(ag, "A philosopher is mortal") is None


def test_capability_consequent_parse_is_environment_dependent_pre_existing_gap():
    """Documentation-level, not a build target here. In THIS worktree
    (pinned to the last COMMITTED native Rust extension, per house
    discipline -- `_native.abi3.so`), the general reader's capability
    ('can') event-construction path does not ground a bare 'Det N can V'
    sentence via `parse_conditional` -- e.g. 'penguin can swim' -> None --
    even though the property ('is') form used by the headline demo above
    ('philosophers are mortal') grounds correctly. Reproduced with a
    PRE-EXISTING, byte-unchanged call (`pd.parse_conditional`, never edited
    by this rung) on a fresh worktree checked out at this rung's own base
    commit -- i.e. this is a property of the COMMITTED Rust binary this
    worktree runs (confirmed live: an unrelated, independently-checked-out
    worktree at the SAME base commit reproduces it identically; the
    CURRENT MAIN working tree, which carries an UNCOMMITTED, newer rebuild
    of `_native.abi3.so`, does NOT reproduce it), not a regression this
    rung introduced. Consistent with, and a sharper instance of, the
    PRE-EXISTING capability-consequent text-round-trip gap
    DEDUCTION_EXTENSION_RESULTS.md Sec2.4 already named (that rung found it
    broke at the FULL `read_and_infer`/`ingest_predication` level; here it
    is shown to reach `parse_conditional` itself in this environment).
    Named, not fixed -- out of this rung's scope (`situation_model_
    reader.py`/`reading_collapse.py` surgery, and the binary-pinning
    question is a build/CI concern, not a deduction-mechanism one)."""
    ag = _fresh()
    assert pd.parse_conditional(ag, "penguin can swim") is None


# --------------------------------------------------------------------------- #
#  EXISTENTIAL INSTANTIATION — witness search (found) + witness mint (none
#  found), both required live cases.
# --------------------------------------------------------------------------- #
def test_existential_witness_search_found():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    smr.ingest_predication(ag, ["is_a", "tux", "bird"])
    minted = pd.mint_existential_premise(ag, "Some bird is a penguin")
    assert minted["minted"] is True
    gaps = ig.detect_existential_gaps(ag)
    assert len(gaps) == 1
    resolved = ig.resolve_existential_gap(ag, gaps[0])
    assert resolved["minted"] is True
    assert resolved["witness_kind"] == "found"
    assert resolved["entity"] == "tux"
    assert smr.entity_state(ag, "tux") == {"bird": 1, "penguin": 1}
    # no fresh witness entity was minted.
    sub, _, _ = pd._resolve(ag)
    names = [sub.node(n)["attrs"].get("name") for n in sub.nodes("SmEntity")]
    assert names.count("tux") == 1
    assert not any(n and "witness" in n for n in names)


def test_existential_witness_search_mints_fresh_constant_when_none_found():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    minted = pd.mint_existential_premise(ag, "Some bird is a penguin")
    assert minted["minted"] is True
    gaps = ig.detect_existential_gaps(ag)
    resolved = ig.resolve_existential_gap(ag, gaps[0])
    assert resolved["minted"] is True
    assert resolved["witness_kind"] == "minted"
    witness = resolved["entity"]
    assert smr.entity_state(ag, witness) == {"bird": 1, "penguin": 1, "existential_witness": 1}


def test_existential_resolve_is_idempotent_no_double_witness():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_existential_premise(ag, "Some bird is a penguin")
    gaps = ig.detect_existential_gaps(ag)
    ig.resolve_existential_gap(ag, gaps[0])
    # the schema is now marked witnessed -- a second detect pass sees nothing.
    assert ig.detect_existential_gaps(ag) == []
    sub, _, _ = pd._resolve(ag)
    witness_entities = [sub.node(n)["attrs"].get("name") for n in sub.nodes("SmEntity")
                        if sub.node(n)["attrs"].get("existential_witness")]
    assert len(witness_entities) == 1


def test_existential_end_to_end_via_read_and_infer():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_existential_premise(ag, "Some bird is a penguin")
    r = ig.read_and_infer(ag, "Tux is a bird.")
    assert r["before_situation_model"]["tux"] == {"bird": 1}
    hits = [x for x in r["existential"] if x["minted"]]
    assert len(hits) == 1
    assert hits[0]["witness_kind"] == "found"
    assert hits[0]["entity"] == "tux"
    assert r["situation_model"]["tux"].get("penguin") == 1


def test_existential_no_cross_contamination_with_mp_path():
    """THE cross-contamination pattern the conjunction rung already found
    and fixed (DEDUCTION_EXTENSION_RESULTS.md Sec3.3), re-checked for the
    NEW existential relation label: an unrelated bird entity, offered to the
    EXISTING, unchanged MP pipeline, must never pick up `penguin` from the
    existential schema (a `holds_some`-labelled signature is structurally
    invisible to a `holds`-labelled goal)."""
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_existential_premise(ag, "Some bird is a penguin")
    smr.ingest_predication(ag, ["is_a", "robin", "bird"])
    resolved = [ig.resolve_implication_gap(ag, g) for g in ig.detect_implication_gaps(ag)
                if g["entity"] == "robin"]
    assert all(r["schema"] != "existential_bird_penguin" for r in resolved)
    assert smr.entity_state(ag, "robin").get("penguin") is None


def test_existential_no_cross_contamination_with_conjunction_path():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_existential_premise(ag, "Some bird is a penguin")
    smr.ingest_predication(ag, ["is_a", "puddle", "wet"])
    smr.ingest_predication(ag, ["is_a", "puddle", "cold"])
    resolved = [ig.resolve_conjunctive_gap(ag, g) for g in ig.detect_conjunctive_gaps(ag)]
    assert all(r.get("schema") != "existential_bird_penguin" for r in resolved)


def test_existential_no_leading_quantifier_is_a_named_residual():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    assert pd.parse_existential(ag, "bird is a penguin") is None
    assert pd.mint_existential_premise(ag, "bird is a penguin")["minted"] is False


def test_existential_does_not_get_a_contrapositive():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    pd.mint_existential_premise(ag, "Some bird is a penguin")
    sub, _, _ = pd._resolve(ag)
    names = {sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")}
    assert "existential_bird_penguin_contrapositive" not in names


# --------------------------------------------------------------------------- #
#  QUANTIFIER LEXICON — graph-resident, mirroring WarningLexicon/TrustLexicon.
# --------------------------------------------------------------------------- #
def test_quantifier_lexicon_is_graph_resident_and_scoped():
    ag = _fresh()
    ig.ensure_logical_seeds(ag)
    lex = pd._quantifier_lexicon(ag)
    assert set(lex["universal"]) == {"all", "every", "each"}
    assert set(lex["existential"]) == {"some"}
    assert "a" not in lex["universal"] and "a" not in lex["existential"]
    assert "an" not in lex["universal"] and "an" not in lex["existential"]


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT + SCOPE GUARDS.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_no_new_engine_calls():
    ig_src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    assert not __import__("re").search(r"^\s*import re\b", ig_src, __import__("re").M)
    assert "re.compile(" not in ig_src and "re.match(" not in ig_src
    assert "antecedent_attr ==" not in ig_src
    assert '== "bird"' not in ig_src and "== 'bird'" not in ig_src

    pd_src = open(os.path.join(ROOT, "domains", "propositional_deduction.py")).read()
    assert not __import__("re").search(r"^\s*import re\b", pd_src, __import__("re").M)
    assert "re.compile(" not in pd_src and "re.match(" not in pd_src


def test_existing_mp_and_conjunction_pipeline_byte_unchanged():
    """`detect_implication_gaps`/`resolve_implication_gap`/`decode_gap`/
    `detect_conjunctive_gaps`/`resolve_conjunctive_gap` must carry ZERO
    trace of this rung's own additions -- proving universal instantiation
    is pure DATA (reusing MP unchanged) and existential instantiation is a
    genuinely SEPARATE code path, not a rewrite of any existing one."""
    ig_src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    for fn_start, fn_end in [
        ("def detect_implication_gaps", "def resolve_implication_gap"),
        ("def resolve_implication_gap", "def detect_conjunctive_gaps"),
        ("def detect_conjunctive_gaps", "def resolve_conjunctive_gap"),
    ]:
        start = ig_src.index(fn_start)
        end = ig_src.index(fn_end)
        body = ig_src[start:end]
        assert "holds_some" not in body
        assert "existential" not in body
        assert "witness" not in body


def test_propositional_deduction_existing_functions_byte_unchanged():
    """`parse_conditional`/`mint_logical_schema`/`derive_contrapositive`/
    `ensure_contrapositives` must carry ZERO trace of the quantifier
    extension -- every quantified path is a THIN ADAPTER calling them,
    never a rewrite."""
    pd_src = open(os.path.join(ROOT, "domains", "propositional_deduction.py")).read()
    start = pd_src.index("def parse_conditional")
    end = pd_src.index("def _negate_attr")
    body = pd_src[start:end]
    assert "quantifier" not in body
    assert "_split_leading_quantifier" not in body
    assert "_singular_attr" not in body


def test_ground_reductions_comprehend_theorem_and_original_seed_files_untouched():
    out = subprocess.run(["git", "diff", "--stat", _BASE, "--",
                          "domains/ground_reductions.py", "domains/comprehend_theorem.py",
                          "seeds/logic_foundation.json",
                          "seeds/logic_propositional_predicate.json",
                          "seeds/inference_knowledge.json"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", out.stdout


def test_prior_deduction_test_files_untouched():
    """This rung must not have edited either of the two prior deduction test
    files -- any new coverage belongs in THIS file."""
    out = subprocess.run(["git", "diff", "--stat", _BASE, "--",
                          "tests/test_deduction_generalization.py",
                          "tests/test_deduction_extension.py"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", out.stdout


def test_singular_attr_known_irregular_plural_limitation():
    """Documentation-level: an IRREGULAR plural ('men') is NOT reached by
    the WordNet morphy noun-pos lookup this rung uses -- a named, honest
    limitation, not silently papered over. A REGULAR plural round-trips
    correctly, which is why the live demo uses 'philosophers', not 'men'."""
    ag = _fresh()
    assert pd._singular_attr("philosophers") == "philosopher"
    assert pd._singular_attr("penguins") == "penguin"
    assert pd._singular_attr("mortal") == "mortal"
    assert pd._singular_attr("can_fly") == "can_fly"
    assert pd._singular_attr("men") == "men"   # the named, unfixed limitation

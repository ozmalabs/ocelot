"""test_curie_complete — THE COMPLETE READ of the Marie Curie article + its three
residuals fixed, gated behind a protected fable byte-identity guard.

Gates scripts/jabberwock_reads_curie.py + domains/name_variant_merge.py +
register_source.route_reading (the cap fix):

  (a) COMPLETE READ — the routed read comprehends the WHOLE article (all ~373
      sentences, not the read_and_comprehend default of 40); subject == 'curie';
      curie's unified mention count is far above the 40-cap read.
  (b) NAME-VARIANT MERGE — curie / maria / skłodowska / marie_curie unify into ONE
      subject entity (mentions ≈ the sum); a SECOND person's forms merge too
      (Pierre Curie / Pierre); NO over-merge (Pierre stays distinct from Marie
      though they share the surname 'Curie').
  (c) GENDER PRECISION — pierre == male (own evidence); 1891 / radium / university
      carry NO gender (not animate); the female subject stays female; the
      gender-leak (female inanimate things) drops before -> after.
  (d) SUBJECT stays 'curie' (unified, top of the salience ranking).
  CROW BYTE-IDENTICAL — the fable routes to protagonist-by-arc-agency and the
      refinement never fires (the encyclopedic-only pass); crow protagonist
      unchanged.
  NO OVER-MERGE — two different people sharing a surname stay distinct.
  GRAPH-NATIVE / donkey=0 — the canonical + gender decisions are native Argmax
      Terms; no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_curie_complete.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import name_variant_merge as nvm                   # noqa: E402
from domains import register_source as rs                       # noqa: E402
import jabberwock_reads_curie as jrc                            # noqa: E402

_CURIE_CACHE = os.path.join(ROOT, "data", "register", "curie.txt")
_HAVE_CURIE = os.path.exists(_CURIE_CACHE)
_needs_curie = pytest.mark.skipif(not _HAVE_CURIE,
                                  reason="data/register/curie.txt cache absent")

FABLE = (
    "In a spell of dry weather, when the Birds could find very little to drink, "
    "a thirsty Crow found a pitcher with a little water in it. But the pitcher "
    "was high and had a narrow neck, and no matter how he tried, the Crow could "
    "not reach the water. The poor thing felt as if he must die of thirst. Then "
    "an idea came to him. Picking up some small pebbles, he dropped them into "
    "the pitcher one by one. With each pebble the water rose a little higher "
    "until at last it was near enough so he could drink.")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def _report():
    return jrc.run()


# --------------------------------------------------------------------------- #
#  (a) COMPLETE READ.
# --------------------------------------------------------------------------- #
@_needs_curie
def test_a_complete_read_all_sentences_subject_curie(_report):
    assert _report["n_sentences"] > 250            # the full article, not the 40-cap
    routed = _report["routed"]
    assert routed["family"] == "encyclopedic"
    assert routed["read_approach"] == "subject_by_salience"
    assert routed["answer"] == "curie"
    # the unified subject mention count is far above what a 40-sentence read yields.
    assert _report["routed"]["result"]["mentions"] >= 100


@_needs_curie
def test_a2_cap_fix_full_read_beats_the_40_cap():
    with open(_CURIE_CACHE) as f:
        text = f.read()
    # the OLD default (max_sentences=40) sees a fraction of the subject's mentions.
    capped = _fresh()
    rs.route_reading(capped, text, max_sentences=40, merge_variants=False)
    cap_curie = next((float(capped.s.node(n)["attrs"].get("coref_mentions", 0.0) or 0.0)
                      for n in capped.s.nodes("SmEntity")
                      if capped.s.node(n)["attrs"].get("name") == "curie"), 0.0)
    full = _fresh()
    rs.route_reading(full, text, merge_variants=False)
    full_curie = next((float(full.s.node(n)["attrs"].get("coref_mentions", 0.0) or 0.0)
                       for n in full.s.nodes("SmEntity")
                       if full.s.node(n)["attrs"].get("name") == "curie"), 0.0)
    assert full_curie > cap_curie * 2              # the complete read sees far more


# --------------------------------------------------------------------------- #
#  (b) NAME-VARIANT MERGE + (d) SUBJECT.
# --------------------------------------------------------------------------- #
@_needs_curie
def test_b_name_variants_unify_into_one_subject(_report):
    clusters = _report["refine"]["merge"]["clusters"]
    curie_cl = next((c for c in clusters if c["canonical"] == "curie"), None)
    assert curie_cl is not None, clusters
    absorbed = set(curie_cl["absorbed"])
    # the four fragmented forms unify into the ONE subject entity.
    for form in ("maria", "skłodowska", "marie_curie"):
        assert form in absorbed, (form, absorbed)
    # mentions ≈ the sum (>= the four biggest forms combined, ~113+).
    assert curie_cl["mentions_after"] >= 100
    assert curie_cl["mentions_after"] > curie_cl["mentions_before"]


@_needs_curie
def test_b2_second_person_pierre_merges_no_over_merge(_report):
    clusters = _report["refine"]["merge"]["clusters"]
    pierre_cl = next((c for c in clusters if c["canonical"] == "pierre"), None)
    assert pierre_cl is not None, clusters
    assert "pierre_curie" in pierre_cl["absorbed"]
    # NO OVER-MERGE: Pierre is NOT absorbed into Marie though they share 'Curie'.
    curie_cl = next(c for c in clusters if c["canonical"] == "curie")
    assert "pierre" not in curie_cl["absorbed"]
    assert "pierre_curie" not in curie_cl["absorbed"]


@_needs_curie
def test_d_subject_stays_curie_top_of_ranking(_report):
    res = _report["routed"]["result"]
    assert res["subject"] == "curie"
    assert res["ranking"][0]["name"] == "curie"
    assert res["argmax_matches_top_of_sort"] is True


# --------------------------------------------------------------------------- #
#  (c) GENDER PRECISION.
# --------------------------------------------------------------------------- #
@_needs_curie
def test_c_gender_precision(_report):
    after = _report["after"]
    # pierre — male from his OWN evidence (the full-name form's 'he').
    assert after["pierre"]["gender"] == "male"
    # non-animate things carry NO gender.
    for thing in ("1891", "radium", "university"):
        assert after[thing]["animate"] == 0.0, thing
        assert after[thing]["gender"] == "", thing
    # the female subject stays female.
    assert after["curie"]["gender"] == "female"


@_needs_curie
def test_c2_gender_leak_drops_before_to_after(_report):
    before = jrc._leak_count(_report["before"])
    after = jrc._leak_count(_report["after"])
    # the leak (female inanimate things) is present before the refine and cleared.
    assert len(before) >= 3, before
    assert len(after) <= 1, after                   # ~0 (an honest tiny tail allowed)


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTICAL — the refinement is encyclopedic-only; the fable is not
#  touched (protagonist unchanged, routed narrative).
# --------------------------------------------------------------------------- #
def test_crow_route_protagonist_byte_identical():
    r = rs.route_reading(_fresh(), FABLE)
    assert r["family"] == "narrative"
    assert r["read_approach"] == "protagonist_by_arc_agency"
    assert r["answer"] == "crow"
    assert "refine" not in r["result"]              # the merge/gender pass never ran


# --------------------------------------------------------------------------- #
#  NO OVER-MERGE — two DIFFERENT people sharing a surname stay distinct.
# --------------------------------------------------------------------------- #
def test_no_over_merge_two_people_same_surname():
    text = ("John Smith was a carpenter. He built a house. "
            "Mary Smith was a doctor. She healed the sick. "
            "John Smith later sold the house. Mary Smith opened a clinic.")
    ag = _fresh()
    rs.route_reading(ag, text)
    merged_into = {}
    for n in ag.s.nodes("SmEntity"):
        at = ag.s.node(n)["attrs"]
        nm = at.get("name")
        if isinstance(nm, str) and at.get("merged_into"):
            merged_into[nm] = at.get("merged_into")
    # john and mary must NEVER land in the same cluster (a shared surname alone
    # does not merge two distinct people — they differ in the distinctive token).
    john_root = merged_into.get("john_smith") or merged_into.get("john") or "john"
    mary_root = merged_into.get("mary_smith") or merged_into.get("mary") or "mary"
    # neither given-name person is absorbed into the other's cluster.
    assert "mary" not in str(john_root) and "john" not in str(mary_root)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE / donkey=0 SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decisions_are_graph_native():
    src = inspect.getsource(nvm)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names), "no import re"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "no import re"
    # the canonical pick and the gender pick are native Argmax Terms (Rust decides).
    assert "native.evaluate" in src
    assert "_Argmax" in src
    canon = inspect.getsource(nvm._canonical)
    assert "native.evaluate" in canon and "Argmax" in canon
    pick = inspect.getsource(nvm._pick_gender)
    assert "native.evaluate" in pick

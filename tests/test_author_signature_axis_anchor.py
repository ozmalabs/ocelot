"""AUTHOR_SIGNATURE_AXIS_ANCHOR -- pins the `_shared_shape` fix.

`domains.reflective_faculty._shared_shape` used to pair rows from two signatures by
RAW LIST POSITION (`sig_a[:n]` vs `sig_b[:n]`), so two structurally-unrelated concepts
whose fired `RelationCue`s happened to land at the same index registered a spurious
`fixed > 0` "shared leaf" (measured live,
`docs/research/engine_substrate/SHAPE_KIND_FIELD_RESULTS.md` section 2.2). It is now
CUE-IDENTITY-KEYED: a row from `sig_a` is paired with a row from `sig_b` only when both
are byte-identical to the same held `RelationCue.relation` tuple -- axis-anchored by
content, the same discipline `analogical_thinking._concept_shape_vector` applies over
its own vocabulary, without changing `author_signature`'s own return contract (left
untouched -- see `AUTHOR_SIGNATURE_AXIS_ANCHOR_PREREG.md` section 2.1 for why its
~10 other callers make that the wrong fix locus).

This file pins both directions: the false positive is gone, and a genuine true
positive (two signatures that really do share a named cue) still connects.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import reflective_faculty as rf                # noqa: E402


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def cues():
    rv = json.load(open(os.path.join(ROOT, "seeds", "relation_vocabulary.json")))
    return {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
            if c.get("type") == "RelationCue"}


def test_unrelated_concepts_no_longer_register_a_spurious_shared_leaf(agent, cues):
    """The exact SHAPE_KIND_FIELD_RESULTS.md section 2.2 repro: self-reference/recursion
    vs symmetry -- genuinely no shared structure. Was fixed=1 (positional accident on the
    'to' token); must now be fixed=0."""
    concept_a_sig = [cues["self_reference"], cues["build_from_prior"], cues["base_case"]]
    d = json.load(open(os.path.join(ROOT, "seeds", "math_capability_shapes.json")))
    sym = next(json.loads(n["attrs"]["signature"]) for n in d["nodes"]
               if n["attrs"].get("name") == "symmetry")
    _res, fixed = rf._shared_shape(agent, concept_a_sig, sym)
    assert fixed == 0, "unrelated concepts must not share a leaf by positional accident"


def test_concepts_sharing_a_named_cue_still_connect(agent, cues):
    """Two signatures that genuinely fire the SAME cues (self_reference,
    build_from_prior), authored in a DIFFERENT order (as two independently-scanned
    concepts would be) -- a true positive the fix must not kill."""
    sig_a = [cues["build_from_prior"], cues["self_reference"], cues["base_case"]]
    sig_b = [cues["self_reference"], cues["bounded"], cues["build_from_prior"]]
    res, fixed = rf._shared_shape(agent, sig_a, sig_b)
    assert fixed > 0
    assert list(cues["self_reference"]) in res
    assert list(cues["build_from_prior"]) in res


def test_pairing_is_order_independent(agent, cues):
    """Axis-anchoring means POSITION must not matter: reversing/shuffling the row
    order of one operand must not change the fixed count."""
    sig_a = [cues["build_from_prior"], cues["self_reference"], cues["base_case"]]
    sig_b_fwd = [cues["self_reference"], cues["bounded"], cues["build_from_prior"]]
    sig_b_rev = list(reversed(sig_b_fwd))
    _res1, fixed1 = rf._shared_shape(agent, sig_a, sig_b_fwd)
    _res2, fixed2 = rf._shared_shape(agent, sig_a, sig_b_rev)
    assert fixed1 == fixed2


def test_capability_axis_residual_still_refuses_cleanly(agent, cues):
    """P2a's accidental refusal (SHAPE_KIND_FIELD_RESULTS.md section 2.1) survives for
    a principled reason now: single-token CapabilityAxis-residual rows never match any
    held RelationCue's multi-token relation tuple."""
    cap_axis_sig = [["scan"], ["gate"], ["focus"], ["route"]]
    faculty_sig = cues["self_reference"] and [cues["build_from_prior"], cues["self_reference"],
                                               cues["bounded"], cues["base_case"]]
    _res, fixed = rf._shared_shape(agent, cap_axis_sig, faculty_sig)
    assert fixed == 0


def test_author_signature_return_contract_unchanged(agent):
    """`author_signature`'s own output format/order is untouched by this fix -- the
    fix locus is `_shared_shape` alone (see PREREG section 2.1). Sanity: it still
    returns a plain list of raw relation-tuples (no wrapping, no padding)."""
    agent.s.add_node("Concept", {
        "name": "probe_recursive_concept",
        "definition": "this idea refers to itself and builds the new from the prior, with a base case",
    })
    sig, defn, cname = rf.author_signature(agent.s, "probe_recursive_concept")
    assert sig, "expected at least one RelationCue to fire"
    for row in sig:
        assert isinstance(row, (list, tuple))
        assert all(isinstance(el, str) for el in row), "still raw scalar relation tuples"
    assert defn and cname == "probe_recursive_concept"


def test_learn_term_for_concern_still_resolves_pinned_decision(agent):
    """P3: the named call site (`learn_term_for_concern`, exercised through
    `author_cost_salience`) still resolves to the SAME term_family the pre-existing
    gate (`tests/test_cost_scheduling.py::test_authored_donkey_zero_...`) pins."""
    from scripts.jabberwock_costs_its_frontier import author_cost_salience
    donkey = {"n": 0}
    agent.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    auth = author_cost_salience(agent)
    assert donkey["n"] == 0
    assert auth["term_family"] == "residual_recurrence"

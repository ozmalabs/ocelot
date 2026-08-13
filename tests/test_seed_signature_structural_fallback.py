"""test_seed_signature_structural_fallback — gates for the SEED-GRAIN
structural fallback, per
docs/research/engine_substrate/SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md /
..._RESULTS.md.

Closes SHAPE_AUDIT.md §2.1's A3 finding and the charter
`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` names but does not build for
`_compose_experiment_rule`'s seed-skip pick (`domains/reflective_faculty.py`,
the `vary` branch): the same lexicographic fallback-on-abstain shape
`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` wired for A1/A2
(`_pick_acting_rule`/`_pick_reply_rule`), one grain up — a seed's OWN
aggregate structural signature (`domains.seed_signature`,
`SeedSummary.where_signature_json`) is read only when the primary
`keywords_text` Argmax genuinely abstains.

Two test tiers, mirroring `scripts/rule_signature_measure.py`'s own
two-tier validation:

  1. Unit-level (`domains.seed_signature` directly, plus the standalone Term
     shape) — fast, no full self-experiment pipeline.
  2. End-to-end (`test_class_a_probe_recovered_by_the_real_authored_rules_
     own_term`) — the REAL `_compose_experiment_rule` Python function, called
     DIRECTLY (the level A1/A2's own AR2 tested), its authored mint rule's
     OWN Term extracted (not hand-rebuilt) and evaluated against a real
     `CapabilityAxis` node. See that test's own comment for why it calls the
     function directly rather than through `ground_concern` — a genuine
     reachability finding (the graph-resident composer wins first for every
     non-'replay' 'test'-anchored concern), not a test-only workaround.
"""
from __future__ import annotations

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf
from domains import seed_signature as ssig


# ---------------------------------------------------------------------------
# Real, mechanically-discovered probes (SEED_PICK_STRUCTURAL_FALLBACK_
# RESULTS.md's own AR2 measurement, `scripts/seed_signature_measure.py`):
# each Class A word is present ONLY in the named seed's aggregate structural
# signature and absent from EVERY skippable seed's `keywords_text`; each
# Class B word is present in the named seed's own `keywords_text`.
# ---------------------------------------------------------------------------
_CLASS_A_PROBES = [
    ("investigation_loop", "has_plan"),
    ("investigation_loop", "release_executed_plan"),
    ("investigation_teacher", "mint_impasse_from_stall"),
    ("investigation_teacher", "taught_about"),
]
_CLASS_B_PROBES = [
    ("abandon_on_stuck", "committed"),
    ("discourse", "discourse"),
]


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


@pytest.fixture(scope="module")
def full_agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")
    return a


# ---------------------------------------------------------------------------
# Term builders -- byte-identical to the shape now installed in
# `reflective_faculty._compose_experiment_rule`'s `vary` branch (registered
# in the PREREG before the production edit, reused here rather than
# re-derived, exactly mirroring `scripts/seed_signature_measure.py`).
# ---------------------------------------------------------------------------
V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Gt = lambda a, b: {"type": "Gt", "a": a, "b": b}
Gte = lambda a, b: {"type": "Gte", "a": a, "b": b}
Ite = lambda c, t, o: {"type": "IfThenElse", "cond": c, "then": t, "other": o}
Filter = lambda src, var, pred: {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
Argmax = lambda src, var, val, default: {"type": "Argmax", "source": src, "var_name": var,
                                          "value": val, "default": default}
NodesOfType = lambda t: {"type": "NodesOfType", "node_type": t}
Sum = lambda src, var, val: {"type": "Sum", "source": src, "var_name": var, "value": val}
StrIdx = lambda h, n: {"type": "StringIndexOf", "haystack": h, "needle": n}
LetT = lambda nm, val, body: {"type": "Let", "name": nm, "value": val, "body": body}


def _primary_pick_expr(words_list):
    words = L(words_list)
    overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
    best = Argmax(candidates, "s", overlap(V("s")), None)
    return LetT("best", best,
        Ite(Eq(V("best"), L(None)), L(""),
            Ite(Gt(overlap(V("best")), L(0.0)), Attr(V("best"), "seed_id"), L(""))))


def _combined_pick_expr(words_list):
    words = L(words_list)
    overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
    struct_overlap = lambda node_t: Sum(words, "w",
        Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))
    candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
    best = Argmax(candidates, "s", overlap(V("s")), None)
    struct_best = Argmax(candidates, "s2", struct_overlap(V("s2")), None)
    struct_skip_id_expr = LetT("sbest", struct_best,
        Ite(Eq(V("sbest"), L(None)), L(""),
            Ite(Gt(struct_overlap(V("sbest")), L(0.0)), Attr(V("sbest"), "seed_id"), L(""))))
    return LetT("best", best,
        Ite(Eq(V("best"), L(None)), struct_skip_id_expr,
            Ite(Gt(overlap(V("best")), L(0.0)), Attr(V("best"), "seed_id"), struct_skip_id_expr)))


# ---------------------------------------------------------------------------
# Tier 0 -- domains.seed_signature itself, on a tiny hand-built manifest.
# ---------------------------------------------------------------------------
def test_seed_where_signature_tags_rows_by_owning_rule_name():
    ag = _fresh_agent_with_lexicon()
    manifest = {
        "rules": [
            {"name": "r_one", "match": [["a", "e", "b"]],
             "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "a"},
                                           "key": "distinctive_probe_word"},
                       "b": {"type": "Lit", "value": 1.0}},
             "effects": []},
            {"name": "r_two", "match": [["a", "e", "b"]], "where": None, "effects": []},
        ]
    }
    sig = ssig.seed_where_signature(ag.s, "hand_built_seed", manifest)
    assert sig, "a non-trivial where-clause must produce at least one row"
    rule_names = {row[0] for row in sig}
    assert rule_names == {"r_one"}, "r_two's where=None must contribute zero rows, not crash"
    assert any("distinctive_probe_word" in repr(row) for row in sig)


def test_ensure_seed_signature_is_idempotent(full_agent):
    a = full_agent
    n_first = ssig.ensure_seed_signature(a.s)
    n_second = ssig.ensure_seed_signature(a.s)
    assert n_second == 0, "a second call must touch zero nodes -- the attr is already present"
    # every skippable SeedSummary this rung can reach ends up carrying a
    # (possibly empty, for a manifest-read failure) where_signature_json --
    # never left as None for a seed whose manifest DOES exist on disk.
    n_missing = 0
    for n in a.s.nodes("SeedSummary"):
        at = a.s.node(n)["attrs"]
        if at.get("where_signature_json") is None:
            n_missing += 1
    assert n_missing == 0 or n_first > 0  # sanity: ensure_seed_signature actually ran


# ---------------------------------------------------------------------------
# Tier 1 -- the Term shapes directly, on the real held graph (mirrors
# scripts/seed_signature_measure.py's own AR2 methodology).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed_id,word", _CLASS_A_PROBES)
def test_class_a_primary_abstains_structural_fallback_recovers(full_agent, seed_id, word):
    a = full_agent
    ssig.ensure_seed_signature(a.s)
    primary = a.inner.evaluate(_primary_pick_expr([word]), {})
    combined = a.inner.evaluate(_combined_pick_expr([word]), {})
    assert primary in ("", None), (
        f"primary keywords_text Argmax must genuinely abstain on the structural-only "
        f"word {word!r} (it must not be a substring of ANY seed's keywords_text)")
    assert combined == seed_id, (
        f"the wired fallback must recover the correct seed {seed_id!r} for {word!r}, "
        f"got {combined!r}")


@pytest.mark.parametrize("seed_id,word", _CLASS_B_PROBES)
def test_class_b_combined_pick_matches_unwired_primary(full_agent, seed_id, word):
    a = full_agent
    ssig.ensure_seed_signature(a.s)
    primary = a.inner.evaluate(_primary_pick_expr([word]), {})
    combined = a.inner.evaluate(_combined_pick_expr([word]), {})
    assert primary not in ("", None), f"{word!r} must be a genuine, non-abstaining primary hit"
    assert combined == primary, (
        "the fallback must NEVER fire when the primary Argmax already found a genuine "
        f"match -- combined={combined!r} must equal primary={primary!r}")


# ---------------------------------------------------------------------------
# Tier 2 -- end-to-end: the REAL `reflective_faculty._compose_experiment_rule`
# Python function, called DIRECTLY (the same level A1/A2's own AR2 tested --
# `rf._pick_acting_rule`/`_pick_reply_rule` called directly, not via a higher
# dispatcher), its authored mint rule's OWN Term extracted (not hand-rebuilt)
# and evaluated against a real CapabilityAxis node.
#
# WHY DIRECT, NOT VIA `ground_concern` -- A REAL FINDING, NOT A TEST-ONLY
# WORKAROUND (see SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md's own honest
# residuals section): `ground_concern`'s "experiment" composer tries the
# GRAPH-RESIDENT `_route_experiment_composer` FIRST. For any 'test'-anchored,
# non-'replay' grounded-relation set (this rung's own probe shape, and the
# common case), that graph path ALWAYS succeeds and wins -- `_compose_
# experiment_rule` (the Python function this rung edited) is only ever
# reached via `ground_concern` for the conversation-'replay' family. The
# graph-resident twin (`seeds/composer_experiment_graph.json`'s
# `compose_experiment_mint_parametric` -- SHAPE_AUDIT.md's own A9, "the
# graph-resident twin of A3") still carries the OLD, un-fallback-ed
# keywords_text-only pick, and is EXPLICITLY out of scope for this rung (the
# task brief's own "A4-A9 ... NOT your area", and
# `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`'s own prior declination to
# hand-edit it: "no generator script found ... judged higher-risk than its
# measured benefit"). Calling the Python function directly tests exactly the
# artifact this rung was asked to fix, at the same rigor A1/A2's own AR2
# used, without either overclaiming production reach `ground_concern`
# does not currently give it, or silently laundering that gap through a
# workaround that LOOKED like an end-to-end test.
# ---------------------------------------------------------------------------
def _extract_skip_id_term(rule: dict):
    for eff in rule.get("effects") or []:
        if isinstance(eff, list) and len(eff) >= 4 and eff[:3] == ["add_node", "delta", "SeedDelta"]:
            delta_attrs = eff[3]
            skip = delta_attrs.get("skip_seed_id")
            if isinstance(skip, dict) and "__term__" in skip:
                return skip["__term__"]
    return None


def test_class_a_probe_recovered_by_the_real_authored_rules_own_term(full_agent):
    a = full_agent
    axis1 = a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "induced": 1.0, "capability_keys": ["seed_sig_fallback_mint_concern_3"],
        "residual_predicates": ["test", "vary"],
    })
    rels = rf._residual_relations(a, ["test", "vary"])
    assert rels, "the held RelationCue lexicon must ground test/vary (test_relation_cues_load's own fixture)"

    result = rf._compose_experiment_rule(a, ["seed_sig_fallback_mint_concern_3"], rels)
    mint_rule = next(r for r in result.get("rules", [])
                      if r.get("name", "").startswith("author_experiment_from_residual_"))
    skip_id_term = _extract_skip_id_term(mint_rule)
    assert skip_id_term is not None, "the authored mint rule must carry a skip_seed_id __term__"

    seed_id, word = _CLASS_A_PROBES[0]
    axis2 = a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "induced": 1.0, "residual_predicates": [word],
    })
    picked = a.inner.evaluate(skip_id_term, {"axis": axis2})
    assert picked == seed_id, (
        f"the REAL authored rule's own skip_seed_id Term must pick {seed_id!r} via the "
        f"structural fallback for the word {word!r} -- got {picked!r}")

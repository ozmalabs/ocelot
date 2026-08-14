"""PROBLEM_DECOMPOSITION_PREREG.md / _RESULTS.md — projection-racing +
decompose-or-refuse for an unseen problem, over `graph_treewidth.py`'s
existing treewidth machinery (unchanged).

Confirms, with real data: (a) a discriminating race — a deliberately-bad
single projection would refuse under a bound a real problem's good
projection clears, and racing both picks the good one, on real minted
`knowledge_logical` deduction schemas, producing a genuine multi-clique
split; (b) the CAN correctness anchor — the general race+decompose path on
a real Bigville resident network reproduces `can_junction_tree.py`'s own
direct treewidth/bags/parent structure exactly; (c) an honest refusal case
— every candidate exceeds the bound on the already-measured N=16
treewidth-15 CAN stress network, `attempted: False`, zero mutation of the
underlying problem's own graph state; (d) bounded, effort-budgeted,
residual-driven refinement (PREREG sec7, a live amendment) — a real
7-schema case where round 0 fails for every candidate, the gap shrinks
over TWO real perturbation rounds until `bound_met`, and a smaller budget
on the SAME scenario honestly reports `budget_exhausted` instead of
silently succeeding; (e) refinement is a genuine no-op (`no_improvement`
immediately) on a domain with no `edge_reason` provenance (the CAN
candidates) — refinement never silently "rescues" a genuinely
maximally-coupled real network.
"""
from __future__ import annotations

import json
import random

import pytest

import substrate_rs as sr
from substrate.boot_core import boot_core
from substrate.seed_loader import engine_rules_only
from domains import dictionary_lexicon as dl
from domains import propositional_deduction as pd
from domains.graph_treewidth import treewidth_bound_check, build_elimination_triangulation
from domains.can_junction_tree import can_network_from_mt
from domains.problem_decomposition import (
    project_can_identity, project_can_complete,
    project_deduction_shared_attr, project_deduction_complete,
    project_situation_model_shared_event,
    race_projections, decompose_or_refuse, decompose_problem,
    perturb_worst_shared_reason, refine_projection,
)
from worlds.bigville_can_beliefs import (
    install_productions, build_resident_can_mt, apply_scenario_evidence,
)

SEED_PATH = "seeds/can_native_reimplementation.json"
CAST_PATH = "seeds/bigville_cast100.json"


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh_agent():
    s, node = boot_core()
    return _Agent(s, node)


def _fresh_resident_mt(resident_index):
    s = sr._native.Substrate()
    install_productions(s)
    manifest = json.load(open(SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    residents = json.load(open(CAST_PATH))["residents"]
    built = build_resident_can_mt(s, residents[resident_index])
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)
    return s, built["mt_node"], built["concepts"]


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_frustrated_draw(inner, seed, n=16, coarse=True, discrete_mode="3state"):
    """Verbatim mirror of test_can_junction_tree.py's own helper -- the SAME
    real N=16 stress construction already measured (treewidth 15,
    CAN_SOLVER_TRACTABILITY_RESULTS.md sec2) -- duplicated here rather than
    imported, matching that file's own local-fixture convention."""
    pair_rng = random.Random(seed * 31 + n)
    field_rng = random.Random(seed * 53 + n)
    mt = inner.add_node("Microtheory", {
        "temperature": 2.0, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(n)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(n):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(n):
        for j in range(i + 1, n):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


# --------------------------------------------------------------------------- #
#  (a) discriminating race + genuine cross-facility multi-clique split, on
#  REAL minted knowledge_logical deduction schemas.
# --------------------------------------------------------------------------- #

FOREST_SENTENCES = [
    "if X is a robin, X is a bird",
    "if X is a bird, X can fly",
    "if X is a fish, X can swim",
    "if X is a fish, X is a vertebrate",
    "if X is a vertebrate, X can breathe",
]


def _mint_forest_schemas(ag):
    nodes = []
    for st in FOREST_SENTENCES:
        r = pd.mint_logical_schema(ag, st)
        assert r["minted"] is True, "real prose must mint via the general reading pipeline: %r" % r
        nodes.append(r["node"])
    return nodes


def test_discriminating_race_on_real_deduction_schemas_and_multi_clique_split():
    ag = _fresh_agent()
    schema_nodes = _mint_forest_schemas(ag)
    sub = ag.s

    good = project_deduction_shared_attr(sub, schema_nodes)
    bad = project_deduction_complete(sub, schema_nodes)

    # The deliberately-bad guess, alone, WOULD refuse under a bound the real
    # problem's good projection clears.
    bad_alone = decompose_or_refuse(bad["nodes"], bad["edges"], bound=1)
    print(f"\nbad-alone (complete K5): treewidth={bad_alone['treewidth']} "
          f"attempted={bad_alone['attempted']}")
    assert bad_alone["attempted"] is False
    assert bad_alone["treewidth"] == 4  # K5 -> treewidth n-1=4

    good_alone = decompose_or_refuse(good["nodes"], good["edges"], bound=1)
    print(f"good-alone (shared-attr forest): treewidth={good_alone['treewidth']} "
          f"attempted={good_alone['attempted']}")
    assert good_alone["attempted"] is True
    assert good_alone["treewidth"] == 1

    # Racing BOTH: the racing step must pick the good one and decompose.
    out = decompose_problem(sub, [good, bad], bound=1)
    print(f"race+decompose: winner={out['winner_projection']} "
          f"treewidth={out['treewidth']} attempted={out['attempted']} "
          f"race_candidates={out['race']['candidates']}")
    assert out["winner_projection"] == "deduction_shared_attr"
    assert out["attempted"] is True
    assert out["treewidth"] == 1

    # Genuine MULTI-CLIQUE split: 5 bags (one per schema), across TWO
    # disconnected trees (robin/bird/fly vs fish/vertebrate/breathe) -- not
    # one bag containing everything.
    assert len(out["bags"]) == 5
    roots = [v for v, p in out["parent"].items() if p is None]
    print(f"bags={ {k: sorted(v, key=repr) for k, v in out['bags'].items()} } "
          f"roots={roots}")
    assert len(roots) == 2, "a forest of two disjoint components must have two roots"
    assert max(len(b) for b in out["bags"].values()) == 2, (
        "every bag in a chain/forest of pairwise-shared-attr edges has size <=2 "
        "-- confirms this is NOT a single trivial all-in-one clique")


# --------------------------------------------------------------------------- #
#  (b) CAN correctness anchor -- general path reproduces can_junction_tree.py's
#  own direct decomposition exactly, on a real Bigville resident network.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("resident_index", [0, 1, 17])
def test_can_identity_projection_reproduces_can_junction_tree_exactly(resident_index):
    s, mt, concepts = _fresh_resident_mt(resident_index)
    net = can_network_from_mt(s, mt)
    assert len(net["nodes"]) == 5

    # can_junction_tree.py's own DIRECT path.
    tw_direct = treewidth_bound_check(net["nodes"], net["edges"], bound=4)
    tri_direct = build_elimination_triangulation(net["nodes"], net["edges"],
                                                   tw_direct["elimination_order"])

    good = project_can_identity(s, mt)
    bad = project_can_complete(s, mt)
    out = decompose_problem(s, [good, bad], bound=4)

    print(f"\nresident #{resident_index}: direct tw={tw_direct['treewidth']} "
          f"general-path tw={out['treewidth']} winner={out['winner_projection']}")
    assert out["winner_projection"] == "can_identity"
    assert out["attempted"] is True
    assert out["treewidth"] == tw_direct["treewidth"] == 2

    # EXACT reproduction: same bags (as sets), same parent structure.
    direct_bags = {k: frozenset(v) for k, v in tri_direct["bags"].items()}
    general_bags = {k: frozenset(v) for k, v in out["bags"].items()}
    assert direct_bags == general_bags, "general-path bags must match can_junction_tree's own exactly"
    assert tri_direct["parent"] == out["parent"], (
        "general-path parent structure must match can_junction_tree's own exactly")
    assert tri_direct["order"] == out["order"]


# --------------------------------------------------------------------------- #
#  (c) honest refusal -- every candidate exceeds the bound on the ALREADY-
#  MEASURED N=16 treewidth-15 CAN stress network.
# --------------------------------------------------------------------------- #

def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return inner


def test_refusal_when_every_candidate_exceeds_bound_zero_mutation():
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=5000, n=16, coarse=True)
    before = {c.value: inner.node(c)["attrs"].get("state") for c in concepts}

    identity = project_can_identity(inner, mt)
    complete = project_can_complete(inner, mt)
    print(f"\nN=16 stress: candidates={[(c['name'], len(c['edges'])) for c in (identity, complete)]}")

    out = decompose_problem(inner, [identity, complete], bound=4)
    print(f"refusal: attempted={out['attempted']} treewidth={out['treewidth']} "
          f"winner={out['winner_projection']} reason={out['reason']}")
    assert out["attempted"] is False
    assert out["treewidth"] >= 15  # heuristic upper bound, real number

    after = {c.value: inner.node(c)["attrs"].get("state") for c in concepts}
    assert before == after, "a refused decomposition must not mutate the PROBLEM's own graph state"


def test_refinement_is_honest_no_improvement_on_can_domain_no_rescue():
    """Refinement must NOT silently rescue a genuinely maximally-coupled real
    network -- the CAN candidates carry no edge_reason (a real
    causal_influence edge has no "reason" to blame), so refine_projection
    must report no_improvement immediately, not fabricate a perturbation."""
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=5001, n=16, coarse=True)
    identity = project_can_identity(inner, mt)

    out = decompose_problem(inner, [identity], bound=4, refine_budget=5)
    print(f"\nCAN refine attempt: stop_reason={out['refinement']['stop_reason']} "
          f"rounds_used={out['refinement']['rounds_used']} attempted={out['attempted']}")
    assert out["attempted"] is False
    assert out["refinement"]["stop_reason"] == "no_improvement"
    assert out["refinement"]["rounds_used"] == 0


# --------------------------------------------------------------------------- #
#  (d) bounded, effort-budgeted, residual-driven refinement -- PREREG sec7.
# --------------------------------------------------------------------------- #

CLIQUE_SENTENCES_A = [
    "if X is a dog, X is an animal",
    "if X is a cat, X is an animal",
    "if X is an ostrich, X is an animal",
    "if X is a shark, X is an animal",
]
CLIQUE_SENTENCES_B = [
    "if X is a truck, X is a vehicle",
    "if X is a scooter, X is a vehicle",
    "if X is a glider, X is a vehicle",
]


def _mint_clique_schemas(ag):
    nodes = []
    for st in CLIQUE_SENTENCES_A + CLIQUE_SENTENCES_B:
        r = pd.mint_logical_schema(ag, st)
        assert r["minted"] is True, "real prose must mint: %r" % r
        nodes.append(r["node"])
    return nodes


def test_bounded_refinement_gap_shrinks_over_two_real_rounds_to_bound_met():
    ag = _fresh_agent()
    schema_nodes = _mint_clique_schemas(ag)
    sub = ag.s
    cand = project_deduction_shared_attr(sub, schema_nodes)

    # Round 0 fails: two overlapping generic-consequent groups ("animal"
    # size-4 clique, "vehicle" size-3 clique) push width to 3 on a bound
    # of 1.
    round0 = decompose_or_refuse(cand["nodes"], cand["edges"], bound=1)
    print(f"\nround0: treewidth={round0['treewidth']} attempted={round0['attempted']}")
    assert round0["attempted"] is False
    assert round0["treewidth"] == 3

    out = decompose_problem(sub, [cand], bound=1, refine_budget=5)
    refine = out["refinement"]
    print(f"refinement log: {refine['log']}")
    print(f"stop_reason={refine['stop_reason']} rounds_used={refine['rounds_used']} "
          f"final_treewidth={out.get('treewidth')}")

    assert refine["stop_reason"] == "bound_met"
    assert refine["rounds_used"] == 2, "must take exactly 2 real perturbation rounds, not 1 (not a toy)"
    # Gap must genuinely SHRINK round over round: 2 -> 1 -> -1 (relative to bound=1).
    gaps = [entry["gap"] for entry in refine["log"]]
    assert gaps == [2, 1, -1], "the residual gap must shrink monotonically each round"
    assert out["attempted"] is True
    assert out["treewidth"] == 0


def test_bounded_refinement_honestly_reports_budget_exhausted():
    """The SAME scenario, a smaller budget: must stop honestly at
    budget_exhausted with the partial progress logged -- never silently
    report success it did not reach."""
    ag = _fresh_agent()
    schema_nodes = _mint_clique_schemas(ag)
    sub = ag.s
    cand = project_deduction_shared_attr(sub, schema_nodes)

    out = decompose_problem(sub, [cand], bound=1, refine_budget=1)
    refine = out["refinement"]
    print(f"\nbudget=1: stop_reason={refine['stop_reason']} "
          f"rounds_used={refine['rounds_used']} log={refine['log']}")
    assert refine["stop_reason"] == "budget_exhausted"
    assert refine["rounds_used"] == 1
    assert refine["log"][-1]["gap"] == 1, "partial progress (gap shrank 2->1) must be logged honestly"
    assert out["attempted"] is False, "must NOT silently report success when the budget ran out first"


def test_refine_budget_zero_is_byte_identical_to_no_refinement():
    """The default (refine_budget=0) must be the exact single-round path --
    no behaviour change for every existing caller who doesn't opt in."""
    ag = _fresh_agent()
    schema_nodes = _mint_clique_schemas(ag)
    sub = ag.s
    cand = project_deduction_shared_attr(sub, schema_nodes)

    direct = decompose_or_refuse(cand["nodes"], cand["edges"], bound=1)
    via_pipeline = decompose_problem(sub, [cand], bound=1)  # refine_budget=0 default
    assert via_pipeline["attempted"] == direct["attempted"] == False
    assert via_pipeline["treewidth"] == direct["treewidth"]
    assert via_pipeline["refinement"] is None


# --------------------------------------------------------------------------- #
#  (bonus) third candidate family -- real situation-model shared-event
#  coupling, discrimination generalizes to this domain too.
# --------------------------------------------------------------------------- #

def test_situation_model_shared_event_projection_discriminates():
    from domains import situation_model_reader as smr
    ag = _fresh_agent()
    smr.read_into_situation_model(ag, "John gave Mary the pen. Mary took the cup.")
    sub = ag.s
    events = sub.nodes("SmEvent")
    assert len(events) >= 2

    good = project_situation_model_shared_event(sub, events)
    assert good["edges"], "a real two-event narrative must produce at least one role-coupling edge"

    bad_edges = [(a, b) for i, a in enumerate(good["nodes"]) for b in good["nodes"][i + 1:]]
    bad = {"name": "sm_complete_overcoupled", "nodes": good["nodes"], "edges": bad_edges}

    out = decompose_problem(sub, [good, bad], bound=1)
    print(f"\nsituation-model race: winner={out['winner_projection']} "
          f"good_edges={len(good['edges'])} bad_edges={len(bad_edges)} "
          f"treewidth={out['treewidth']}")
    assert out["winner_projection"] == good["name"]

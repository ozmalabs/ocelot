"""BigvilleCanBeliefs -- per-resident Causal Attitude Network (CAN) builder
(seeds/bigville_can_beliefs.json).

WORLD-ADAPTER / SEED-BUILDER work only: mechanically translates one
``bigville_cast100.json`` resident record's already-drawn ``params`` dict
into a personal, individually-parameterized CAN belief network (one
``Microtheory`` + 5 ``Concept`` nodes + 5 ``causal_influence`` edges) on a
live ``substrate_rs.Substrate``. Every formula here is a FIXED mechanical
translation from a resident's real drawn params to graph data -- the same
class of operation as ``bigville_town100_world.generate_cast100`` itself
(``experiments/gamma-substrate/CLAUDE.md``: "population seeding is
MECHANICAL world setup = data"). No conditional over any agent's graph
VALUATION; no rule engine; no agent decision.

The 5 Concept topics and 5 structural edges are grounded in ALREADY-WIRED
Bigville mechanics, not invented (file:line citations in the module-level
docstrings below and in
``docs/research/engine_substrate/BIGVILLE_CAN_INTEGRATION_PREREG.md`` sec1.5):

  * ``trust_mayor`` / ``claim_credible`` mirror
    ``seeds/bigville_drama_social.json``'s ``bd_villager_backs`` rule
    (``:534-560``): ``cred_john = seen_benevolent*charm_weight -
    seen_hostile*hostile_weight`` vs. ``cred_mary =
    heard_claim*(claim_weight - difficulty_penalty)`` -- the SAME param
    names ``bigville_cast100.json``'s ``_PARAM_SPEC`` already draws.
  * ``debtor_trustworthy`` mirrors ``seeds/bigville_loop_reputation.json``'s
    ``bl_townsfolk_opinion`` (``:13-232``): ``standing`` vs.
    ``badmouthed*badmouth_weight``.
  * ``world_safe`` / ``self_worth`` directly mirror the ``prior_world_safe``
    / ``prior_self_worth`` foundational IWM priors (Bowlby --
    ``bigville_town_seed.py:60-64``'s own comment).

RESOLUTION mechanism: each edge's "true" continuous coupling (a fixed
structural base + a small per-resident nuance term from that resident's OWN
drawn param) is QUANTIZED to the resident's ``effective_bins`` vocabulary --
the exact k-level-vocabulary mechanism
``CAN_BELIEF_QUANTIZATION_PREREG.md`` sec2.2 already registered and
``CAN_BELIEF_QUANTIZATION_RESULTS.md`` already measured, now driven by the
real per-resident ``resolution_bins`` TRAIT (``bigville_cast100.json``)
composed with the existing arousal-driven ``resolution_level`` STATE
(``bigville_motivation.json``'s ``mv_arousal``) instead of a hand-set
experimental condition.
"""
from __future__ import annotations

# ---- the 5-topic template (same names for every resident; DISTINCT nodes
# per resident -- can_ops.rs stores sigma/h/identity as attrs ON the Concept
# node, so sharing a node across residents would share their belief state).
TOPIC_NAMES = [
    "trust_mayor", "claim_credible", "world_safe", "self_worth",
    "debtor_trustworthy",
]

# ---- structural edge template: (concept_a, concept_b, base_J, nuance_key)
# base_J is the fixed, general structural relationship (same conceptual
# claim for every resident); nuance_key names the resident's OWN drawn param
# whose deviation from the population mean nudges the "true" coupling --
# keeps the "true" relationship resident-specific without inventing a fresh
# per-pair random draw (mirrors CAN_BELIEF_QUANTIZATION_PREREG.md sec2.2's
# "same true draw, only the encoding differs" isolation discipline).
STRUCTURAL_EDGES = [
    ("trust_mayor", "claim_credible", -0.6, "mood_bias"),
    ("trust_mayor", "world_safe", 0.5, "w_supergraph"),
    ("world_safe", "self_worth", 0.5, "mood_bias"),
    ("claim_credible", "debtor_trustworthy", 0.4, "w_supergraph"),
    ("trust_mayor", "debtor_trustworthy", 0.3, "mood_bias"),
]

# population means for the nuance params (bigville_town100_world._PARAM_SPEC)
_POP_MEAN = {"mood_bias": 0.30, "w_supergraph": 0.50}
_NUANCE_CLIP = 0.15
_NUANCE_SCALE = 0.3


def effective_resolution_bins(resolution_bins_trait: float, arousal: float,
                               res_gain: float = 1.0) -> int:
    """Trait ceiling x state fraction, re-quantized to the integer lattice.

    ``resolution_level`` reuses ``bigville_motivation.json``'s own
    ``mv_arousal`` formula verbatim: ``max(0, 1 - res_gain*arousal)`` --
    high arousal narrows how much of the trait ceiling is currently usable.
    Floored at 2 (below 2 bins there is no discriminable distinction --
    the same floor the trait's own mixture draw is clamped to).
    """
    resolution_level = max(0.0, 1.0 - res_gain * arousal)
    bins = round(resolution_bins_trait * resolution_level)
    return max(2, int(bins))


def quantize_j(true_j: float, bins: int) -> float:
    """Round ``true_j`` (continuous, expected in [-1,1]) to the nearest of
    ``bins`` evenly-spaced levels across [-1,1] -- the same k-level
    vocabulary-quantization mechanism
    ``CAN_BELIEF_QUANTIZATION_PREREG.md`` sec2.2 registered (coarse:
    ``k in {-1,0,+1}``, 3 values; fine: 9 values), generalized from a fixed
    2-level experimental manipulation to a per-resident-real integer."""
    if bins <= 1:
        return 0.0
    levels = [-1.0 + 2.0 * i / (bins - 1) for i in range(bins)]
    return min(levels, key=lambda lv: abs(lv - true_j))


def true_edge_j(params: dict, base_j: float, nuance_key: str) -> float:
    """The 'true' (un-quantized) continuous coupling for one structural
    edge: the fixed structural base plus a small per-resident nuance term
    drawn from that resident's OWN already-drawn param's deviation from the
    population mean (clipped to +-0.15 so the base relationship dominates)."""
    pop_mean = _POP_MEAN[nuance_key]
    dev = params.get(nuance_key, pop_mean) - pop_mean
    nuance = max(-_NUANCE_CLIP, min(_NUANCE_CLIP, dev * _NUANCE_SCALE))
    return max(-1.0, min(1.0, base_j + nuance))


def install_productions(s) -> None:
    """Install the Gamma admissibility-grammar productions
    ``seeds/bigville_can_beliefs.json`` declares as data, mechanically (same
    shape as ``tests/test_can_ops.py``'s own ``_fresh_substrate`` fixture --
    this is data application, not a new decision)."""
    for src_t, et, tgt_t in (
        ("Resident", "has_belief_mt", "Microtheory"),
        ("Microtheory", "has_concept", "Concept"),
        ("Concept", "causal_influence", "Concept"),
    ):
        s.add_production({
            "src": {"type": src_t, "var": "src"},
            "edge_type": et,
            "tgt": {"type": tgt_t, "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "bigville_can_beliefs",
        })


def build_resident_can_mt(s, resident: dict, res_gain: float = 1.0,
                           beta: float = 1.5) -> dict:
    """Mint one resident's personal CAN belief Microtheory on live substrate
    ``s`` (productions already installed via ``install_productions``).
    Mechanical translation only -- every value written is a fixed function
    of the resident's own already-drawn ``params`` dict.

    Returns a dict: ``resident_node``, ``mt_node``, ``concepts`` (topic ->
    NodeID), ``effective_bins``, and ``edges`` (list of dicts with the
    endpoints, ``true_j``, and ``quantized_j`` -- for the rounding-error
    manipulation check).
    """
    p = resident["params"]
    eff_bins = effective_resolution_bins(p["resolution_bins"], p["arousal"], res_gain)

    r = s.add_node("Resident", {
        "name": resident["name"], "index": resident["index"],
        "resolution_bins": p["resolution_bins"], "arousal": p["arousal"],
        "effective_bins": eff_bins,
    })
    mt = s.add_node("Microtheory", {
        "name": "%s_beliefs" % resident["name"], "temperature": beta,
    })
    s.add_edge(r, "has_belief_mt", mt, {})

    concepts = {}
    for name in TOPIC_NAMES:
        concepts[name] = s.add_node("Concept", {"name": name})
        s.add_edge(mt, "has_concept", concepts[name], {})

    # identity fields (long-standing priors -- continuous personality attrs,
    # NOT quantized; scaled from [0,1] priors to [-1,1]).
    s.set_attr(concepts["world_safe"], "identity_field", 2.0 * (p["prior_world_safe"] - 0.5))
    s.set_attr(concepts["self_worth"], "identity_field", 2.0 * (p["prior_self_worth"] - 0.5))
    s.set_attr(concepts["trust_mayor"], "identity_field",
               (p["charm_weight"] - p["hostile_weight"]) * 0.5
               + 0.5 * (p["prior_others_trust"] - 0.5))
    # cred_on (bigville_town100_world._PARAM_SPEC: mean=1.0, sd=0.2, clip
    # lo=0.0 hi=None) as a GAIN on the whole credibility signal, not an
    # additive term -- byte-identical at the population mean (cred_on=1.0),
    # and non-negative by construction (clip lo=0.0) so it scales magnitude
    # without flipping sign. This is the real consumer the seed's own
    # docstring already named ("h seeded from claim_weight, cred_on,
    # w_supergraph") but the formula had never actually read.
    s.set_attr(concepts["claim_credible"], "identity_field",
               p.get("cred_on", 1.0) * ((p["claim_weight"] - 1.0) * 0.5
                                        + (p["w_supergraph"] - 0.5)))
    s.set_attr(concepts["debtor_trustworthy"], "identity_field",
               -p["w_spite"] + (p["prior_others_trust"] - 0.5))

    edges = []
    for a, b, base_j, nuance_key in STRUCTURAL_EDGES:
        true_j = true_edge_j(p, base_j, nuance_key)
        q_j = quantize_j(true_j, eff_bins)
        # Symmetric pair (CAN_NATIVE_REIMPLEMENTATION_RESULTS.md sec7's
        # named, verified-backward-compatible fix): the native discrete-
        # async rule's local-field Sum(Edges(c,"causal_influence")) reads
        # OUT-edges only, so a Concept whose only coupling was an IN-edge
        # (e.g. claim_credible's edge FROM trust_mayor) was invisible to
        # it. Minting both directions with the SAME weight makes every
        # coupling visible as an out-edge from EITHER endpoint. This is
        # additive-risk-only for the existing continuous mechanism --
        # build_couplings's in-edge de-dup (can_ops.rs:180-191) and
        # enumerate_couplings's undirected-pair de-dup (can_ops.rs:293-322)
        # both already skip a neighbour already found via the other
        # direction, so mt_mean_field_marginal/audit_basin's own
        # coupling_count/energy/frustration arithmetic is unchanged.
        s.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": q_j})
        s.add_edge(concepts[b], "causal_influence", concepts[a], {"weight": q_j})
        edges.append({"a": a, "b": b, "true_j": true_j, "quantized_j": q_j})

    return {
        "resident_node": r, "mt_node": mt, "concepts": concepts,
        "effective_bins": eff_bins, "edges": edges,
    }


# ---- the shared scenario evidence applied identically to any two networks
# being compared (BIGVILLE_CAN_INTEGRATION_PREREG.md sec6): "the town
# witnesses a public, hostile confrontation between Mary and John."
SCENARIO_EVIDENCE = (
    ("claim_credible", 1.0, 0.6),
    ("trust_mayor", -0.6, 0.6),
)


def apply_scenario_evidence(s, concepts: dict) -> None:
    """Apply the SAME scenario evidence to a resident's Concept nodes, via
    the existing ``concept_apply_evidence`` PyO3 op (mechanical, no new
    mutation logic)."""
    for topic, evidence, alpha in SCENARIO_EVIDENCE:
        s.concept_apply_evidence(concepts[topic], evidence, alpha)

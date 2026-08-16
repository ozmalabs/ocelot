"""can_self_worth_bridge -- sources SelfPattern.held_self_worth from a
resident's REAL, live, PERSISTENT CAN self_worth belief instead of a
hand-picked scalar.

Per docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md and
PERSISTENT_SELF_WORTH_PREREG.md. Pure world-adapter/harness code (CLAUDE.md's
architecture rule): builds a resident's real CAN Microtheory
(worlds/bigville_can_beliefs.py), relaxes it via the engine's OWN
discrete-asynchronous update rule (seeds/can_native_reimplementation.json's
can_native_update_3state, under run_rules()), and reads the converged
self_worth Concept's `state` back. No decision is made here -- the relaxed
belief IS the engine's own Hopfield-style fixpoint, not a Python
computation. A resident appraised more than once on the SAME substrate
REUSES their one persistent network (find_or_build_resident_can) rather
than minting a fresh, reset one each call, and record_incident_outcome
feeds an already-decided appraisal back as evidence so the belief genuinely
drifts across repeated incidents -- the SAME concept_apply_evidence PyO3 op
apply_scenario_evidence already established, mechanically re-applied.

REAL ENGINE GOTCHA (PERSISTENT_SELF_WORTH_PREREG.md Sec1, found live):
concept_apply_evidence mutates external_field OUTSIDE the rule-effect path,
so run_rules()'s incremental dirty-tracking never re-examines the Concept
afterward -- confirmed directly: even a massive evidence application left
`state` unchanged (steps=0) until `force_all_dirty()` was called first.
Every evidence-then-relax call in this module calls it -- do not remove it.

No seed is edited by this module -- can_native_reimplementation.json is
loaded and consumed exactly as tests/test_can_native_reimplementation.py's
own _build_draw / test_bigville_schema_symmetric_fix_makes_all_couplings_
visible_to_native_rule already do.
"""
from __future__ import annotations

from worlds import bigville_can_beliefs as bcb


def _find_resident_node(inner, name: str):
    for node in inner.nodes("Resident"):
        if inner.node(node)["attrs"].get("name") == name:
            return node
    return None


def _concepts_for_resident(inner, resident_node):
    mt = inner.neighbours(resident_node, "has_belief_mt")[0]
    concepts = {}
    for concept in inner.neighbours(mt, "has_concept"):
        concepts[inner.node(concept)["attrs"]["name"]] = concept
    return mt, concepts


def find_or_build_resident_can(inner, resident: dict, *, max_steps: int = 3000) -> dict:
    """The PERSISTENT entry point (PERSISTENT_SELF_WORTH_PREREG.md Sec2):
    if `resident["name"]` already has a Resident node on this substrate,
    reuse its EXISTING Microtheory/Concepts (the SAME network, carrying
    whatever `self_worth` it has drifted to from prior incidents) instead
    of minting a fresh, reset one. Only a genuinely NEW resident gets
    initialized (state/external_field=0.0, discrete_mode='3state') and
    relaxed for the first time. Returns {resident_node, mt, concepts,
    self_worth, steps, is_new}.
    """
    existing = _find_resident_node(inner, resident["name"])
    if existing is not None:
        mt, concepts = _concepts_for_resident(inner, existing)
        steps = inner.run_rules(max_steps)
        self_worth = inner.node(concepts["self_worth"])["attrs"]["state"]
        return {"resident_node": existing, "mt": mt, "concepts": concepts,
                "self_worth": self_worth, "steps": steps, "is_new": False}

    built = bcb.build_resident_can_mt(inner, resident)
    mt = built["mt_node"]
    concepts = built["concepts"]
    # build_resident_can_mt sets identity_field but not state/external_field
    # (confirmed by reading it directly, HELD_SELF_WORTH_FROM_CAN_PREREG.md
    # Sec2) -- initialize them here, mirroring tests/test_can_native_
    # reimplementation.py::_build_draw's own convention exactly.
    for concept in concepts.values():
        inner.set_attr(concept, "state", 0.0)
        inner.set_attr(concept, "external_field", 0.0)
    inner.set_attr(mt, "discrete_mode", "3state")
    inner.set_attr(mt, "can_tick", 0)
    steps = inner.run_rules(max_steps)
    self_worth = inner.node(concepts["self_worth"])["attrs"]["state"]
    return {"resident_node": built["resident_node"], "mt": mt, "concepts": concepts,
            "self_worth": self_worth, "steps": steps, "is_new": True}


def relax_resident_self_worth(inner, resident: dict, *, max_steps: int = 3000) -> dict:
    """Backward-compatible name for find_or_build_resident_can's own
    {self_worth, concepts, mt, steps} shape (HELD_SELF_WORTH_FROM_CAN_
    RESULTS.md's original callers) -- now PERSISTENT: a second call for the
    same resident name reuses the existing, possibly-drifted network."""
    out = find_or_build_resident_can(inner, resident, max_steps=max_steps)
    return {"self_worth": out["self_worth"], "concepts": out["concepts"],
            "mt": out["mt"], "steps": out["steps"]}


def record_incident_outcome(inner, concepts: dict, *, standard_met: bool,
                            attribution_locus: str, alpha: float = 0.3,
                            max_steps: int = 3000):
    """Feed an ALREADY-DECIDED self-conscious appraisal back as evidence on
    the resident's OWN self_worth Concept (PERSISTENT_SELF_WORTH_PREREG.md
    Sec2) -- no new decision, standard_met/attribution_locus were already
    decided by the dispute/self-conscious chain. Gated on attribution_locus
    != 'circumstance': an outcome not attributed to the self at all should
    not move the self-concept (Lewis 1971; Miller 1996) -- a real
    theoretical claim, not an incidental scoping choice. Returns the
    (possibly unchanged) current self_worth state; None input attribution_
    locus is never valid (callers always have a decided one).

    `alpha` IS belief plasticity (DOMAIN_SELF_WORTH_PROJECTION_PREREG.md
    Sec4b) -- Dweck's fixed-vs-growth-mindset axis: a LOW alpha resident's
    domain belief barely moves even after many same-sign incidents (fixed
    mindset / "does not learn that"); a HIGH alpha resident's decouples
    from the global-belief projection within 1-2. This is a PERSONALITY
    TRAIT, not a fixed constant -- a caller should read it from
    `resident["params"]` (the SAME convention prior_self_worth/w_supergraph/
    w_spite already use) and pass it here explicitly, exactly as every
    other trait in this file already flows from data to a mechanical PyO3
    call. The 0.3 default exists ONLY for callers (this module's own prior
    rungs) that predate this trait and never varied it.

    RETRACTED, checked and reverted before shipping (EVIDENCE_AND_AUDIENCE_
    WEIGHTING_PREREG.md Sec1/RESULTS Sec1): `alpha / (domain_incident_count
    + 1)` was tried and measured -- it reproduces the count-divided
    (`1/n`) learning-rate anti-pattern CLAUDE.md's own F-16 retrospective
    already diagnosed ("1/n asserts stationarity... each rate needs a
    rate") -- the harmonic series diverges so slowly that a belief this
    formula governs takes ~200 incidents to flip, not the "still learns,
    just slower" the PREREG registered. Caught before shipping, not after.
    `alpha` stays UNWEIGHTED, applied flat -- exactly as `DOMAIN_SELF_
    WORTH_PROJECTION_PREREG.md` originally established it, unchanged.

    MUST call force_all_dirty() before re-running -- concept_apply_evidence
    writes external_field outside the rule-effect path and run_rules()'s
    incremental dirty-tracking will otherwise silently no-op (PREREG Sec1,
    found live; regression-tested).
    """
    self_worth_concept = concepts["self_worth"]
    if attribution_locus == "circumstance":
        return inner.node(self_worth_concept)["attrs"]["state"]
    evidence = 1.0 if standard_met else -1.0
    inner.concept_apply_evidence(self_worth_concept, evidence, alpha)
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return inner.node(self_worth_concept)["attrs"]["state"]


def _existing_domain_self_worth_count(inner, mt) -> int:
    count = 0
    for concept in inner.neighbours(mt, "has_concept"):
        name = inner.node(concept)["attrs"].get("name", "")
        if name.startswith("self_worth:"):
            count += 1
    return count


def mint_domain_self_worth(inner, resident_can: dict, domain: str, *,
                           base_coupling: float = 0.6, max_steps: int = 3000):
    """Domain-scoped self-worth as PROJECTION-THEN-DECOUPLING
    (DOMAIN_SELF_WORTH_PROJECTION_PREREG.md Sec2-3) -- Rotter (1954)'s
    generalized-vs-specific-expectancy mechanism, implemented with ZERO new
    Rust/rules: a domain Concept with NO independent prior
    (identity_field=0.0 -- a domain never faced before has none) coupled
    (both directions, mirroring STRUCTURAL_EDGES' own convention) to the
    resident's GLOBAL self_worth Concept. The FIRST relaxation has nothing
    else to go on but that coupling, so the domain Concept's state settles
    to whatever the global Concept's CURRENT state is -- projection,
    mechanically, via the SAME can_native_update_3state formula every other
    Concept in this arc already uses. record_incident_outcome, called with
    {"self_worth": <the returned domain Concept>}, then accumulates
    domain-specific evidence there (not on the global Concept) -- once that
    outweighs the coupling term, the domain belief decouples and reflects
    its own track record instead (Rotter's specific expectancy displacing
    the generalized one).

    The COUPLING STRENGTH is not a flat constant (SELF_COMPLEXITY_COUPLING_
    PREREG.md): `coupling_weight = base_coupling / (existing_domain_count +
    1)` -- Linville (1985, 1987)'s self-complexity buffering, weighted
    against a REAL, observed graph quantity (how many domains this
    resident has already differentiated), Laplace-style ("+1, made up when
    absent" -- a resident's first domain gets the FULL base_coupling,
    matching the un-audited original behavior exactly). Given this
    engine's own already-measured discrete-3-state threshold
    (DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md Sec2 point 5, ~0.366 at
    temperature=1.5), this is a SHARP step under the current mechanism,
    not a graded one -- registered and accepted, not smoothed over.

    Idempotent: a second call for the same resident_can + domain name
    returns the EXISTING Concept (whatever it has drifted to), never a
    freshly reset one -- mirrors find_or_build_resident_can's own
    discipline exactly.

    `resident_can` is find_or_build_resident_can's own return dict (needs
    "mt" and "concepts"["self_worth"]). `domain` is a plain label (e.g.
    "public_speaking") -- the Concept is named "self_worth:<domain>".
    """
    mt = resident_can["mt"]
    global_self_worth = resident_can["concepts"]["self_worth"]
    concept_name = "self_worth:%s" % domain
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing

    existing_domain_count = _existing_domain_self_worth_count(inner, mt)
    coupling_weight = base_coupling / (existing_domain_count + 1)

    domain_concept = inner.add_node("Concept", {
        "name": concept_name, "state": 0.0, "external_field": 0.0,
        "identity_field": 0.0,
    })
    inner.add_edge(mt, "has_concept", domain_concept, {})
    inner.add_edge(global_self_worth, "causal_influence", domain_concept,
                   {"weight": coupling_weight})
    inner.add_edge(domain_concept, "causal_influence", global_self_worth,
                   {"weight": coupling_weight})
    inner.force_all_dirty()
    inner.run_rules(max_steps)
    return domain_concept


def mint_domain_reparative_desire(inner, resident_can: dict, domain: str):
    """Idempotent: the resident's `reparative_desire_for:<domain>` Concept
    (SELF_CONSCIOUS_CONSEQUENCE_PREREG.md Sec2) -- guilt's motivational
    consequence (Tangney & Dearing 2002: guilt attributes to a specific
    act and motivates REPARATIVE action toward whoever was affected). A
    fresh, UNCOUPLED accumulator (unlike mint_domain_self_worth's
    projected-then-decoupling design) -- a reparative urge is not a
    generalized expectancy, it starts at 0.0 with no prior."""
    mt = resident_can["mt"]
    concept_name = "reparative_desire_for:%s" % domain
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing
    concept = inner.add_node("Concept", {
        "name": concept_name, "state": 0.0, "external_field": 0.0,
        "identity_field": 0.0,
    })
    inner.add_edge(mt, "has_concept", concept, {})
    return concept


def mint_domain_withdrawal_desire(inner, resident_can: dict, domain: str):
    """Idempotent: the resident's `withdrawal_desire_for:<domain>` Concept
    (SELF_CONSCIOUS_CONSEQUENCE_PREREG.md Sec2) -- shame's motivational
    consequence (Tangney & Dearing 2002: shame attributes to the global
    self and motivates WITHDRAWAL/avoidance/hiding). Same fresh,
    uncoupled shape as mint_domain_reparative_desire."""
    mt = resident_can["mt"]
    concept_name = "withdrawal_desire_for:%s" % domain
    for existing in inner.neighbours(mt, "has_concept"):
        if inner.node(existing)["attrs"].get("name") == concept_name:
            return existing
    concept = inner.add_node("Concept", {
        "name": concept_name, "state": 0.0, "external_field": 0.0,
        "identity_field": 0.0,
    })
    inner.add_edge(mt, "has_concept", concept, {})
    return concept


def record_self_conscious_consequence(inner, resident_can: dict, domain: str, *,
                                      emotion: str, alpha: float = 0.3,
                                      max_steps: int = 3000) -> dict:
    """Route evidence to guilt's or shame's own motivational consequence,
    keyed on the ALREADY-DECIDED `emotion` (SelfConsciousSignal.emotion,
    self_conscious_emotions.json's own sc_decide_emotion rule) --
    SELF_CONSCIOUS_CONSEQUENCE_PREREG.md Sec2. No decision made here: the
    dispatch is a literal string match on a value the substrate's OWN
    rule already decided, the same shape HATE_PITY_TOM_UNDERSTANDING_
    PREREG.md's consequence_route dispatch and record_incident_outcome's
    own `attribution_locus == "circumstance"` check already use.

    hubristic_pride/authentic_pride/embarrassment/none apply evidence to
    NEITHER Concept -- a specific gate, not a catch-all.

    Returns {"consequence": "reparative"|"withdrawal"|None,
    "reparative_desire_state", "withdrawal_desire_state"} (external_field
    of each Concept, minting lazily on first use so an untouched Concept
    reads 0.0 rather than requiring the caller to pre-mint both)."""
    consequence = None
    if emotion == "guilt":
        concept = mint_domain_reparative_desire(inner, resident_can, domain)
        inner.concept_apply_evidence(concept, 1.0, alpha)
        inner.force_all_dirty()
        inner.run_rules(max_steps)
        consequence = "reparative"
    elif emotion == "shame":
        concept = mint_domain_withdrawal_desire(inner, resident_can, domain)
        inner.concept_apply_evidence(concept, 1.0, alpha)
        inner.force_all_dirty()
        inner.run_rules(max_steps)
        consequence = "withdrawal"

    reparative_concept = mint_domain_reparative_desire(inner, resident_can, domain)
    withdrawal_concept = mint_domain_withdrawal_desire(inner, resident_can, domain)
    return {
        "consequence": consequence,
        "reparative_desire_state": inner.node(reparative_concept)["attrs"]["external_field"],
        "withdrawal_desire_state": inner.node(withdrawal_concept)["attrs"]["external_field"],
    }


def mint_peer_comparison_context(inner, domain_concept):
    """Idempotent: the domain Concept's own PeerComparisonContext, minted
    once (RELATIVE_SELF_WORTH_PREREG.md Sec2). Reused by
    record_peer_observation/read_relative_self_worth on every later call
    for this same domain Concept."""
    existing = inner.neighbours(domain_concept, "has_peer_comparison")
    if existing:
        return existing[0]
    ctx = inner.add_node("PeerComparisonContext", {})
    inner.add_edge(domain_concept, "has_peer_comparison", ctx, {})
    return ctx


def record_peer_observation(inner, peer_context, *, peer_did_well: bool,
                            max_steps: int = 3000):
    """Mechanically record ONE observation of another resident's outcome
    in this domain (RELATIVE_SELF_WORTH_PREREG.md Sec2) -- a real,
    SEPARATE evidence channel from the resident's own incidents
    (record_incident_outcome, untouched). Whether the peer did well is
    caller-supplied data (what was actually observed/heard), exactly as
    every other input in this arc has been; the log-odds DECISION is
    still entirely the engine's own compute_relative_self_worth rule."""
    outcome = "did_well" if peer_did_well else "did_poorly"
    obs = inner.add_node("PeerObservation", {"outcome": outcome})
    inner.add_edge(peer_context, "has_observation", obs, {})
    inner.run_rules(max_steps)
    return obs


def read_relative_self_worth(inner, domain_concept) -> float:
    """The engine's own computed relative_self_worth (domain state minus
    the peer-comparison log-odds baseline) -- what SelfPattern.
    held_self_worth should be sourced from going forward
    (RELATIVE_SELF_WORTH_PREREG.md Sec2), not the raw domain state alone.
    Falls back to the raw domain state if no PeerComparisonContext has
    ever been minted for this Concept (zero real or fictional comparison
    data at all -- distinct from the zero-observations-but-minted case,
    which the engine's own rule already resolves to state-minus-0.0)."""
    attrs = inner.node(domain_concept)["attrs"]
    if "relative_self_worth" in attrs:
        return attrs["relative_self_worth"]
    return attrs["state"]


def ensure_peer_comparison_seed(inner) -> None:
    """Idempotently load seeds/peer_comparison.json (depends_on
    can_native_reimplementation, loaded first via ensure_can_seed)."""
    import json
    from substrate.seed_loader import engine_rules_only

    ensure_can_seed(inner)
    if inner.nodes("PeerComparisonSeedLoaded"):
        return
    d = json.load(open("seeds/peer_comparison.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    inner.add_node("PeerComparisonSeedLoaded", {})


def ensure_can_seed(inner) -> None:
    """Idempotently load seeds/can_native_reimplementation.json and install
    worlds/bigville_can_beliefs.py's Gamma productions -- the two pieces a
    caller needs on the substrate BEFORE calling relax_resident_self_worth.
    Guarded by rule_count() so a caller that already loaded the seed (or is
    composing multiple bridges on one substrate) does not reload it."""
    import json
    from substrate.seed_loader import engine_rules_only

    if inner.nodes("CanSelfWorthBridgeSeedLoaded"):
        bcb.install_productions(inner)
        return
    d = json.load(open("seeds/can_native_reimplementation.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    bcb.install_productions(inner)
    inner.add_node("CanSelfWorthBridgeSeedLoaded", {})


__all__ = ["relax_resident_self_worth", "find_or_build_resident_can",
           "record_incident_outcome", "mint_domain_self_worth", "ensure_can_seed",
           "mint_peer_comparison_context", "record_peer_observation",
           "read_relative_self_worth", "ensure_peer_comparison_seed"]

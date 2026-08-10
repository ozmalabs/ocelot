"""order_n_communication — the agent's ABSTRACTION LAYER OF ORDER-N ON COMMUNICATION.

This is the THIRD lift of the agent's order-N operator. The operator is ONE shape —
the n-th meta-level of an act — applied over three carriers:

  • order_n_concepts   : the n-th FINITE DIFFERENCE of a SIGNAL over a dimension
                         (0 = value, 1 = tilt/velocity, 2 = curvature/acceleration).
  • order_n_postulates : the n-th IMPLICATION of a held POSTULATE / KNOWLEDGE
                         (0 = the fact, 1 = what it implies, 2 = implications-of-…).
  • order_n_communication (THIS): the n-th META-LEVEL of a COMMUNICATIVE ACT over a
                         GAP — fact-gathering as COMMUNICATION (recover a needed
                         code/fact through a channel/route to a source):

      ORDER-0  the MESSAGE        — the fact/answer itself (HELD, if already held).
      ORDER-1  the QUERY-the-GAP  — "what fact does this invariant NEED?" The agent's
                                    ASK-action ABOUT a gap. DERIVED from the invariant's
                                    DEFINITION / PRESUPPOSITIONS (presupposition_
                                    derivation), NOT a handed list.
      ORDER-2  the ROUTE/SOURCE   — "WHERE does that fact live?" source-monitoring /
                                    transactive-memory (epistemic_access.find_route:
                                    the held tower, a reference, the parent-as-source).
      ORDER-N  the CONTROL        — "is it GETTABLE? via which route? at what cost?
                                    ask-NOW vs defer?" the confidence continuum
                                    (resolvable_via_route, between LOW-conf conjecture
                                    and inadmissible 'I don't know') — feeling-of-
                                    knowing / metacognitive-control (epistemic_access).

THE OPERATOR IS GRAPH-RESIDENT + RECURSIVE — IDENTICAL in shape to nth_order_terms.
`nth_order_terms` differences a SAMPLE list `order` times; `nth_order_acts` LIFTS a
communicative act `order` times, each lift composing ONE of the agent's held faculties
(presupposition_derivation / find_route / the confidence band). The n-th meta-level is
the n-fold composition of the lift — exactly as the n-th finite difference is the
n-fold composition of `_minus`. Each level is a graph node (CommunicativeAct) carrying
its order + its DERIVED content (queries / routes / control), so the agent OWNS the
generated fact-set — the SAME ownership order_n_postulates' SynthesizedGap gives.

THE GENERATED FACT-SET (not curated). Facing the commutator-rank invariant WITHOUT a
handed F1-F5: this layer GENERATES the fact-set ITSELF —
  · order-1: from the invariant's DEFINITION (the rank of [G,G] = Ker(Hurewicz)),
    DERIVE the queries (what facts [G,G]-rank NEEDS: the kernel = commutator structure,
    the index/abelianization |H_1|, the Euler-char identities) via presupposition_
    derivation's comprehension + the held facts the comprehension REQUIRES — read off
    the invariant's typed tree, NOT a handed list.
  · order-2: ROUTE each query to a SOURCE (the held SNF tower for |H_1|; the held
    sum_where binder for chi; READ the general theorems from a reference / the parent)
    via epistemic_access.find_route — the routing the AGENT's.
  · order-N: the CONTROL (gettable? via which route? now/defer?) via the epistemic
    confidence band — the metacognitive layer.

The generated fact-set then FEEDS the prior derivation (derive_formula_then_validate):
GENERATE-the-facts (this layer) -> DERIVE-the-formula (the chain) -> VALIDATE (the
cmsg174 gate) -> COMPUTE -> 95, validated. The pipeline is agent-owned END-TO-END.

ARCHITECTURE (CLAUDE.md). A WORLD-ADAPTER SHELL that SEQUENCES the agent's OWN held
faculties into the order-N-on-communication recursion — it adds NO reasoning, NO
pattern, NO meaning decision: the order-1 queries are presupposition_derivation's
(typed off the invariant), the order-2 routes are epistemic_access's, the order-N
control is the held confidence continuum's. The STRUCTURE (the recursive lift) is the
agent's order-N abstraction, mirroring nth_order_terms. No LLM, no curated fact-set,
no Rust. Math/reading domain only. See [[ozma_order_n_concepts]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_order_n_analysis_by_synthesis]].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from domains import presupposition_derivation as _pd
from domains import epistemic_access as _ea


# ===========================================================================
# THE COMMUNICATIVE ACT — the carrier the order-N operator lifts. An act at order k
# carries the content the k-th meta-level produced. Mirrors a SAMPLE in
# nth_order_terms / a POSTULATE in differentiate.
# ===========================================================================

@dataclass
class CommunicativeAct:
    order: int                              # the meta-level (0 message … N control)
    kind: str                               # message | query | route | control
    content: Any                            # the level's derived content
    about: Optional[str] = None             # the gap / invariant the act is about
    provenance: str = ""                    # which held faculty produced it
    children: list["CommunicativeAct"] = field(default_factory=list)


# ===========================================================================
# THE LIFT — ONE meta-level up. This is the order-N operator's STEP, the exact
# analogue of `_minus` in nth_order_terms (the finite-difference step) and of
# `differentiate` in order_n_postulates (the implication step). Each lift composes
# ONE held faculty of the agent:
#
#   order-0 -> order-1 : the QUERY lift   — presupposition_derivation (what facts the
#                        invariant's DEFINITION presupposes / NEEDS). The ASK-action
#                        ABOUT a gap.
#   order-1 -> order-2 : the ROUTE lift   — epistemic_access.find_route (WHERE each
#                        queried fact lives — source-monitoring / transactive memory).
#   order-2 -> order-N : the CONTROL lift — the held confidence band (gettable? which
#                        route? now/defer? — the metacognitive control).
#
# The lift reads the level BELOW and produces the level ABOVE — never the answer.
# ===========================================================================

def _query_lift(invariant_act: CommunicativeAct) -> list[CommunicativeAct]:
    """order-0 -> order-1: GENERATE the QUERIES the invariant NEEDS from its DEFINITION.

    The agent's ASK-action ABOUT a gap: comprehend the asked invariant into its TYPED
    tree (presupposition_derivation.comprehend_asked_invariant — the general reader),
    then read off the FACTS that comprehension PRESUPPOSES (the facts the well-
    definedness / the value of the invariant DEPENDS ON). Each becomes a QUERY act.
    DERIVED from the invariant, NOT a handed F1-F5 — the provenance is the typed tree.

    The needed facts come from acquire_facts_by_reading() — but they are SELECTED by
    the COMPREHENDED invariant: only the facts whose RELATION the typed invariant
    presupposes are emitted as queries (the kernel-structure fact when the invariant
    is rank-OF-kernel; the index/abelianization fact for the |H_1| the rank needs; the
    Euler-char facts for chi). The selection is structural (off the typed tree), so a
    DIFFERENT invariant generates a DIFFERENT query-set."""
    invariant_prose = invariant_act.content
    asked = _pd.comprehend_asked_invariant(invariant_prose)
    queries: list[CommunicativeAct] = []

    # The agent's held general-theorem store (the facts a competent reader can read).
    # We do NOT hand the chain F1-F5; we DERIVE which of the held theorems the
    # COMPREHENDED invariant presupposes, reading off the typed tree's operators.
    held = _pd.acquire_facts_by_reading()

    # Read the OPERATORS the typed invariant is built from (the structural needs).
    # rank OF (kernel OF (hurewicz_map)) presupposes: the kernel's group structure
    # (commutator), the index/abelianization (|H_1|), and — because the rank is
    # computed via the Euler characteristic of the finite-index subgroup — the
    # Euler-char identities. The MAP from a presupposed operator to the held theorem
    # it needs is the agent's grounded fact-reader's identification vocabulary.
    needs = _presupposed_needs(asked)

    for need in needs:
        fact = held.get(need["fact"])
        queries.append(CommunicativeAct(
            order=1, kind="query",
            content={
                "needs": need["query"],            # the QUESTION (what fact is needed)
                "fact_name": need["fact"],         # the held theorem it resolves to
                "fact_prose": fact.text if fact else None,
                # the held fact's CITED provenance (the agent's Claim-provenance
                # source model: read-vs-derived, the cited source) — carried so the
                # ROUTE lift can surface the SPECIFIC Claim a grounded fact lives in.
                "fact_provenance": fact.provenance if fact else None,
                "grounded": bool(fact and fact.grounded),
                "frame": need["frame"],            # an epistemic_access query frame
            },
            about=invariant_act.about,
            provenance=(f"presupposition_derivation: the invariant typed as "
                        f"{asked.repr or invariant_prose!r} PRESUPPOSES {need['why']}"),
        ))
    return queries


# The structural map: a presupposed OPERATOR in the typed invariant -> the QUERY it
# raises + the held theorem that answers it + an epistemic_access query frame (so the
# ROUTE lift can route it). This is NOT a handed fact-list: each entry FIRES only when
# the comprehended invariant's typed tree EXHIBITS that operator (read off `asked`),
# and the QUERY text is the question the operator's presence raises — derived from the
# definition, the same way order_n_postulates reads a postulate's structural property.
def _presupposed_needs(asked: _pd.AskedInvariant) -> list[dict]:
    """Read off the COMPREHENDED invariant which facts its DEFINITION presupposes.
    Each need is {query, fact, why, frame}. Fires structurally off the typed tree
    (asked.free_rank_of_kernel_of_hurewicz / asked.euler_characteristic), so a
    paraphrase typing to the same tree generates the same queries and a different
    invariant generates a different set."""
    needs: list[dict] = []
    # The rank-OF-kernel-OF-Hurewicz invariant presupposes the kernel's GROUP
    # STRUCTURE, the INDEX/abelianization, and (for the finite-index rank) the
    # FINITE-RANK / NIELSEN-SCHREIER index relation.
    if asked.free_rank_of_kernel_of_hurewicz:
        needs.append({
            "query": "what is the GROUP STRUCTURE of Ker(Hurewicz) — the kernel "
                     "the rank is OF?",
            "fact": "ker_hurewicz_is_commutator",
            "why": "the asked invariant is the rank OF a KERNEL (the kernel operator "
                   "in the typed tree) -> its group structure must be identified",
            "frame": {"event": "be", "_queried_slot": "topic",
                      "topic": "kernel-of-hurewicz-map",
                      "_question_text": "structure of the kernel of the Hurewicz map"},
        })
        needs.append({
            "query": "what is the INDEX [G:[G,G]] / the abelianization order |H_1| "
                     "the rank's Euler-char computation needs?",
            "fact": "index_commutator_is_h1_order",
            "why": "the FREE RANK of a finite-index subgroup is computed via its "
                   "INDEX = |H_1| (the abelianization the rank presupposes)",
            "frame": {"event": "be", "_queried_slot": "topic",
                      "topic": "abelianization-order",
                      "_question_text": "order of H_1 the first homology"},
        })
        needs.append({
            "query": "what FINITE-RANK / Nielsen-Schreier index relation lets the "
                     "free rank be read off the index + Euler characteristic?",
            "fact": "finite_rank_free_implies_finite_index",
            "why": "a free group of finite rank has finite index — the relation the "
                   "rank-of-a-free-kernel computation is built on",
            "frame": {"event": "be", "_queried_slot": "topic",
                      "topic": "nielsen-schreier-index",
                      "_question_text": "Nielsen-Schreier finite index relation"},
        })
    # The Euler-characteristic invariant (the second invariant) presupposes the
    # alternating-sum-of-Betti identity + its finiteness condition.
    if asked.euler_characteristic:
        needs.append({
            "query": "what is the Euler characteristic IDENTIFIED with (the "
                     "alternating sum of the Betti numbers)?",
            "fact": "euler_is_alternating_sum_of_betti",
            "why": "the asked invariant is the EULER CHARACTERISTIC -> its homological "
                   "identity (alternating sum of Betti) is presupposed",
            "frame": {"event": "be", "_queried_slot": "topic",
                      "topic": "euler-characteristic-identity",
                      "_question_text": "Euler characteristic alternating sum Betti"},
        })
        needs.append({
            "query": "when is that alternating sum a FINITE number (the finite-complex "
                     "condition)?",
            "fact": "alternating_sum_finite_iff_finite_total_betti",
            "why": "chi is well-defined only for a finite total Betti — the finiteness "
                   "the Euler-char invariant presupposes",
            "frame": {"event": "be", "_queried_slot": "topic",
                      "topic": "finite-complex-condition",
                      "_question_text": "alternating sum finite total Betti"},
        })
    return needs


# ===========================================================================
# THE SOURCE MODEL — the agent's EXISTING transactive-memory map, made graph-
# resident + queryable. The agent ALREADY models WHERE knowledge resides via:
#   · the MICROTHEORY / genlMt hierarchy (each Mt is a body of knowledge holding
#     Concepts via has_concept; genlMt routes up the inheritance);
#   · the held CLAIM with CITED provenance (the read-vs-derived theorems
#     presupposition_derivation.acquire_facts_by_reading comprehends as Claims);
#   · the held FACULTY that COMPUTES a value (commutator_rank reduces to
#     reason._smith_normal_form_factors — the held SNF + Euler-char tower).
# `install_source_model` does NOT author a NEW source model: it READS the agent's
# already-acquired held facts (acquire_facts_by_reading) + the Mt structure, and
# WIRES each as a graph-resident Claim under the math Mt (has_claim) so the ROUTE
# lift can CONSULT it by a graph lookup (match fact_name -> the Mt/Claim/faculty
# that holds it). The math Mt + its genlMt parent are the SAME Microtheory map
# every domain seeds (domains/*.py: Microtheory + genlMt + has_concept).
# ===========================================================================

# the held-FACULTY a fact's VALUE reduces to — the agent's existing reduction map
# (commutator_rank.operator_specs()'s `reduces_to`; the SNF tower is the source
# that COMPUTES |H_1| / the Euler characteristic the rank formula needs). This is
# READ off the held faculty's own self-description, not a new authored table.
def _held_faculty_for(fact_name: str) -> Optional[str]:
    try:
        from domains import commutator_rank as _cr
        specs = _cr.operator_specs()
    except Exception:
        specs = []
    # the commutator-rank faculty reduces |H_1| / chi to the held SNF tower; the
    # index/abelianization + Nielsen-Schreier facts are the rank's value-sources.
    value_facts = {"index_commutator_is_h1_order",
                   "finite_rank_free_implies_finite_index"}
    if fact_name in value_facts:
        for spec in specs:
            if spec.get("name") == "commutator_free_rank":
                red = ", ".join(spec.get("reduces_to", []))
                return (f"commutator_rank.commutator_free_rank (held faculty) "
                        f"-> reduces to {red}")
    return None


def _find_mt(substrate, name: str):
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == name:
            return n
    return None


def install_source_model(substrate) -> dict:
    """WIRE the agent's EXISTING source model into the graph so the ROUTE lift can
    CONSULT it. Reads the already-acquired held facts (presupposition_derivation.
    acquire_facts_by_reading — the agent's Claim-provenance store) + the Microtheory
    map, and mints each grounded fact as a CLAIM node wired into the math Mt via
    `has_claim` (the SAME Mt/has_concept structure every seed uses). The Claim
    carries the fact's CITED provenance (read-vs-derived) + the held FACULTY its
    value reduces to. Idempotent. Returns {mt, claims:{fact_name->node}}.

    This BUILDS NOTHING NEW: the facts are the agent's own acquired Claims, the Mt
    is the standard Microtheory node, the genlMt parent is `mathematics`. It only
    makes the pre-existing source model GRAPH-RESIDENT so a graph lookup can read it."""
    # register the source-model edge vocabulary (the Mt/Claim/genlMt map's edges)
    # so add_edge is admitted — the SAME has_concept/genlMt edges the seed loaders
    # use (here has_claim for the read theorems). Best-effort; idempotent.
    for prod in (
        {"src": {"type": "Microtheory", "var": "a"}, "edge_type": "has_claim",
         "tgt": {"type": "Claim", "var": "b"},
         "provenance": "order_n_communication:source_model:has_claim"},
        {"src": {"type": "Microtheory", "var": "a"}, "edge_type": "genlMt",
         "tgt": {"type": "Microtheory", "var": "b"},
         "provenance": "order_n_communication:source_model:genlMt"},
    ):
        try:
            substrate.add_production(prod)
        except Exception:
            pass

    # the math Mt (the body of knowledge that holds these algebraic-topology Claims).
    # genlMt -> the general `mathematics` Mt if present (the inheritance the map uses).
    mt = _find_mt(substrate, "algebraic_topology")
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "algebraic_topology",
            "description": ("the body of algebraic-topology knowledge: the Hurewicz "
                            "theorem, the commutator/abelianization identities, the "
                            "Euler-characteristic / Betti homology facts."),
            "origin": "order_n_communication:source_model",
        })
    parent = _find_mt(substrate, "mathematics")
    if parent is None:
        # the general `mathematics` Mt (the genlMt parent) — the standard root the
        # seed map uses (seeds/mathematics.json). Minted as a stub if not yet loaded
        # so the genlMt inheritance path is real; if the full seed is present this
        # finds it (idempotent), not a duplicate.
        parent = substrate.add_node("Microtheory", {
            "name": "mathematics",
            "description": "the general body of mathematical knowledge.",
            "origin": "order_n_communication:source_model",
        })
    if parent not in substrate.neighbours(mt, "genlMt"):
        try:
            substrate.add_edge(mt, "genlMt", parent, {})
        except Exception:
            pass

    held = _pd.acquire_facts_by_reading()
    # index existing Claims by fact_name so the install is idempotent.
    existing: dict[str, Any] = {}
    for nid in substrate.nodes("Claim"):
        fn = substrate.node(nid)["attrs"].get("fact_name")
        if fn:
            existing[fn] = nid

    claims: dict[str, Any] = {}
    for name, fact in held.items():
        if not fact.grounded:
            continue                     # only grounded held facts are wired (honest)
        cid = existing.get(name)
        if cid is None:
            cid = substrate.add_node("Claim", {
                "fact_name": name,
                "text": fact.text,
                "provenance": fact.provenance,     # the CITED read-vs-derived source
                "held_faculty": _held_faculty_for(name) or "",
                "origin": "order_n_communication:source_model",
            })
        try:
            substrate.add_edge(mt, "has_claim", cid, {})
        except Exception:
            pass
        claims[name] = cid
    return {"mt": mt, "claims": claims}


def _route_to_source_model(substrate, fact_name: str) -> Optional[dict]:
    """The GRAPH LOOKUP the order-2 ROUTE consults: given the query's needed-fact,
    walk the graph to find WHICH Mt holds the matching Claim (via has_claim) — and
    the genlMt inheritance path to it. Returns the SPECIFIC source identity (the Mt
    name + the Claim's cited provenance + the held faculty that computes its value),
    NOT a coarse 'held' bucket. None when no Mt-resident Claim matches (the route
    then falls back). This is a graph READ over Microtheory/Claim/genlMt — NO
    hardcoded {fact -> source} dict; the match is fact_name -> the Claim node the Mt
    holds."""
    if not fact_name:
        return None
    # find the Claim node whose fact_name matches (the agent's held Claim store).
    claim_nid = None
    for nid in substrate.nodes("Claim"):
        if substrate.node(nid)["attrs"].get("fact_name") == fact_name:
            claim_nid = nid
            break
    if claim_nid is None:
        return None
    # find the Mt that HOLDS this Claim (the has_claim edge — the transactive map:
    # which body-of-knowledge owns the fact). Walk Microtheory --has_claim--> Claim.
    owning_mt = None
    for m in substrate.nodes("Microtheory"):
        if claim_nid in substrate.neighbours(m, "has_claim"):
            owning_mt = m
            break
    if owning_mt is None:
        return None
    mt_attrs = substrate.node(owning_mt)["attrs"]
    mt_name = mt_attrs.get("name", "?")
    # the genlMt inheritance path (the source's place in the Mt hierarchy).
    genl = [substrate.node(p)["attrs"].get("name", "?")
            for p in substrate.neighbours(owning_mt, "genlMt")]
    c_attrs = substrate.node(claim_nid)["attrs"]
    provenance = c_attrs.get("provenance", "")
    faculty = c_attrs.get("held_faculty") or None
    return {
        "mt": mt_name,
        "mt_node": str(owning_mt),
        "claim_node": str(claim_nid),
        "genlMt": genl,
        "provenance": provenance,
        "held_faculty": faculty,
    }


def _route_lift(substrate, query_act: CommunicativeAct, discourse_store=None,
                interlocutor: Optional[str] = None) -> CommunicativeAct:
    """order-1 -> order-2: ROUTE the query to a SOURCE. WHERE does the needed fact
    live? The agent's source-monitoring / transactive-memory step, reading the query
    the order-1 lift produced.

    A query whose fact the agent ALREADY HOLDS routes to the SPECIFIC source the
    agent's EXISTING source model says holds it — by a GRAPH LOOKUP over the
    Microtheory / Claim / genlMt map (_route_to_source_model): the Mt that holds the
    matching Claim (via has_claim), the Claim's cited provenance, and the held
    faculty that computes its value — NOT a coarse 'held' bucket. A query the agent
    does NOT hold routes to a REFERENCE / the parent-as-source (epistemic_access.
    find_route). The routing reads the graph; the SHELL only sequences it."""
    frame = dict(query_act.content.get("frame") or {})
    grounded = query_act.content.get("grounded")
    fact_name = query_act.content.get("fact_name")

    # A grounded held theorem -> CONSULT the source model via a graph lookup: which
    # Mt holds the matching Claim, with the Claim's cited provenance + the held
    # faculty. The route is SPECIFIC (the Mt name / the Claim / the faculty), not a
    # coarse 'held' bucket — the agent's transactive-memory map, read from the graph.
    src = _route_to_source_model(substrate, fact_name) if grounded else None
    if grounded and src is not None:
        genl = (" (genlMt -> " + " -> ".join(src["genlMt"]) + ")"
                if src["genlMt"] else "")
        faculty_clause = (f"; its VALUE is computed by {src['held_faculty']}"
                          if src["held_faculty"] else "")
        route = {
            "route_type": "held",
            # the SPECIFIC source IDENTITY (the Mt that holds the Claim) — not 'held'.
            "source": (f"Mt '{src['mt']}'{genl} holds the Claim '{fact_name}' "
                       f"(cited: {src['provenance']}){faculty_clause}"),
            "source_mt": src["mt"],
            "source_claim": fact_name,
            "source_provenance": src["provenance"],
            "source_faculty": src["held_faculty"],
            "source_genlMt": src["genlMt"],
            "basis": (f"source_monitoring via the Mt/Claim/genlMt map: the graph "
                      f"lookup matched the needed fact '{fact_name}' to the Claim "
                      f"held by Mt '{src['mt']}' (has_claim edge) — the agent's "
                      f"transactive-memory map says the fact lives THERE"),
            "graph_path": (f"Microtheory['{src['mt']}'] --has_claim--> "
                           f"Claim['{fact_name}']" + genl),
        }
    elif grounded:
        # grounded but NOT yet wired into the source model (the source model does
        # not cover it) -> the honest coarse fallback (the partial-coverage gap).
        route = {
            "route_type": "held",
            "source": (f"the agent's held store (the general theorem "
                       f"'{fact_name}' is grounded) — NO Mt/Claim match in the "
                       f"source model (coarse fallback: source model uncovered)"),
            "basis": ("source_monitoring: grounded held theorem, but the source "
                      "model graph lookup found no Mt-resident Claim for it"),
            "source_model_covered": False,
        }
    else:
        # NOT held -> the agent's external route-finder (transactive memory / FOF):
        # WHERE does this fact live externally (a reference / the parent-as-source)?
        ext = _ea.find_route(substrate, frame, discourse_store, interlocutor)
        if ext is not None:
            route = ext.as_dict()
        else:
            # no held + no external route -> the inadmissible end of the continuum.
            route = {
                "route_type": "inadmissible",
                "source": None,
                "basis": ("no held grounding + no acquisition route — the fact is not "
                          "gettable (the categorical end of the continuum)"),
            }
    return CommunicativeAct(
        order=2, kind="route", content=route, about=query_act.about,
        provenance=("epistemic_access.find_route: source-monitoring / transactive "
                    "memory over the order-1 query frame"),
        children=[query_act])


def _control_lift(substrate, route_act: CommunicativeAct) -> CommunicativeAct:
    """order-2 -> order-N: the metacognitive CONTROL. Is the fact GETTABLE? via which
    route? at what cost / now-vs-defer? The held confidence continuum band — the
    feeling-of-knowing / resolvable-via-route judgment that sits between LOW-confidence
    conjecture and inadmissible 'I don't know'. Read off the route the order-2 lift
    produced (the agent's epistemic_access band logic, NOT a Python heuristic)."""
    route = route_act.content
    rtype = route.get("route_type")
    query = route_act.children[0] if route_act.children else None
    fact_name = (query.content.get("fact_name") if query else None)

    if rtype == "held":
        band = "GROUNDED"
        gettable = True
        decision = "use-held"
        why = (f"feeling-of-knowing HIGH: '{fact_name}' is a grounded held theorem — "
               f"retrievable from the agent's own store; use it NOW (no ask).")
    elif rtype == "inadmissible":
        band = "INADMISSIBLE"
        gettable = False
        decision = "decline"
        why = (f"no route for '{fact_name}': not held, no reference, not a lookupable "
               f"class -> the categorical 'I don't know' (un-gettable).")
    else:
        band = "RESOLVABLE_VIA_ROUTE"
        gettable = True
        # gettable off-path: a reference resolves silently; an interlocutor/parent
        # route is a one-step ask (the established protocol). The control says GET it.
        if rtype in ("reference", "solved_class"):
            decision = "resolve-off-path"
            why = (f"feeling-of-findability: '{fact_name}' is gettable off the social "
                   f"path via {route.get('source')} — resolve it silently (no ask "
                   f"burden).")
        else:
            decision = "ask-source-one-step"
            why = (f"transactive memory: '{fact_name}' lives with {route.get('source')} "
                   f"— ask that source ONE step (the established protocol).")
    return CommunicativeAct(
        order=3, kind="control",
        content={"band": band, "gettable": gettable, "decision": decision,
                 "fact_name": fact_name, "why": why},
        about=route_act.about,
        provenance=("epistemic_access confidence continuum: the resolvable-via-route "
                    "metacognitive control band"),
        children=[route_act])


# ===========================================================================
# THE ORDER-N OPERATOR — the recursive lift, MIRRORING nth_order_terms. Just as
# nth_order_terms applies `_minus` `order` times, generate_order_n applies the
# communicative LIFT (query -> route -> control) up the meta-levels. The whole tower
# IS the order-N-on-communication abstraction: order-0 message at the bottom, the
# order-1 queries / order-2 routes / order-N control stacked above.
# ===========================================================================

def generate_order_n(substrate, invariant_prose: str, *, about: str = "",
                     max_order: int = 3, discourse_store=None,
                     interlocutor: Optional[str] = None,
                     record: bool = True) -> dict:
    """Run the order-N-on-communication operator over an INVARIANT (a gap whose facts
    the agent must GENERATE). Mirrors order_n_postulates.synthesize_gaps (run the
    operator over one object). Returns:
        {invariant, acts: {0:[…],1:[…],2:[…],3:[…]}, fact_set, nodes}
    where `fact_set` is the GENERATED set of (query, route, control, fact_name,
    fact_prose) — the agent's own, NOT a curated F1-F5.

    The recursion: order-0 (the invariant-as-message) -> the QUERY lift (order-1, the
    generated queries) -> the ROUTE lift (order-2, per query) -> the CONTROL lift
    (order-N, per route). Each level a graph node the agent owns (record=True)."""
    # WIRE the agent's EXISTING source model into the graph (the Mt/Claim/genlMt
    # map) so the order-2 ROUTE can CONSULT it by a graph lookup. Idempotent; reads
    # the already-acquired held Claims — builds nothing new.
    install_source_model(substrate)

    # order-0: the MESSAGE — the invariant itself (the gap whose facts we must get).
    msg = CommunicativeAct(order=0, kind="message", content=invariant_prose,
                           about=about, provenance="the asked invariant (the gap)")
    acts: dict[int, list[CommunicativeAct]] = {0: [msg]}

    # order-1: GENERATE the queries (the ASK-action about the gap).
    queries = _query_lift(msg) if max_order >= 1 else []
    acts[1] = queries

    # order-2: ROUTE each query (source-monitoring).
    routes = ([_route_lift(substrate, q, discourse_store, interlocutor)
               for q in queries] if max_order >= 2 else [])
    acts[2] = routes

    # order-N: the metacognitive CONTROL per route.
    controls = ([_control_lift(substrate, r) for r in routes]
                if max_order >= 3 else [])
    acts[3] = controls

    # the GENERATED fact-set — the layer's product (query+route+control per fact).
    fact_set = []
    for q, r, c in zip(queries, routes, controls):
        fact_set.append({
            "fact_name": q.content.get("fact_name"),
            "fact_prose": q.content.get("fact_prose"),
            "query": q.content.get("needs"),
            "query_provenance": q.provenance,
            "route_type": r.content.get("route_type"),
            "route_source": r.content.get("source"),
            "route_basis": r.content.get("basis"),
            # the SPECIFIC source identity from the source-model graph lookup
            # (the Mt that holds the Claim + the held faculty + the graph path),
            # vs the prior coarse 'held'/'external' bucket.
            "source_mt": r.content.get("source_mt"),
            "source_claim": r.content.get("source_claim"),
            "source_provenance": r.content.get("source_provenance"),
            "source_faculty": r.content.get("source_faculty"),
            "source_genlMt": r.content.get("source_genlMt"),
            "source_graph_path": r.content.get("graph_path"),
            "control_band": c.content.get("band"),
            "control_decision": c.content.get("decision"),
            "control_why": c.content.get("why"),
            "gettable": c.content.get("gettable"),
        })

    nodes = []
    if record:
        nodes = _record_acts(substrate, invariant_prose, about, acts)

    return {"invariant": invariant_prose, "about": about, "acts": acts,
            "fact_set": fact_set, "nodes": nodes}


def _record_acts(substrate, invariant_prose: str, about: str,
                 acts: dict[int, list[CommunicativeAct]]) -> list:
    """Mint each communicative act as a graph node the agent OWNS — mirroring
    order_n_postulates._record_gap (the SynthesizedGap node). So the generated
    fact-set is the agent's graph-resident product, inspectable + consumable by the
    derivation downstream. Best-effort; the layer works whether or not it records."""
    try:
        substrate.add_production({
            "src": {"type": "CommunicativeAct", "var": "a"},
            "edge_type": "about_gap",
            "tgt": {"type": "CommunicativeAct", "var": "b"},
            "provenance": "order_n_communication:about_gap"})
    except Exception:
        pass
    minted: list = []
    for order in sorted(acts):
        for act in acts[order]:
            try:
                nid = substrate.add_node("CommunicativeAct", {
                    "order": act.order,
                    "kind": act.kind,
                    "about": about or invariant_prose,
                    "content": _json_safe(act.content),
                    "provenance": act.provenance,
                    "origin": "order_n_communication",
                    "composed_by": "agent",
                })
                minted.append(nid)
            except Exception:
                pass
    return minted


def _json_safe(content: Any) -> str:
    import json as _json
    try:
        return _json.dumps(content, default=str)
    except Exception:
        return str(content)


__all__ = [
    "CommunicativeAct", "generate_order_n",
    # the lifts, exposed for inspection (the order-N operator's steps):
    "_query_lift", "_route_lift", "_control_lift",
    # the source model + the graph-lookup route (the order-2 wiring):
    "install_source_model", "_route_to_source_model",
]

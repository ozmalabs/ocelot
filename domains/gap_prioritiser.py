"""gap_prioritiser — the agent RANKS its own synthesized gaps IN THE GRAPH.

order_n_postulates gives the agent a gap DETECTOR (synthesize_gaps): it derives a
set of SynthesizedGap nodes from its own postulates. The autopoietic loop then needs
the agent to PICK WHICH gap to pursue next. That PICK is REASONING (which gap closes
the most of my knowledge), so — per the architecture rule (memory
[[ozma_concepts_in_gamma]]: ALL reasoning is graph-resident Term-trees; Python only
RUNS the graph + interfaces world<->graph) — it lives as a graph-resident Term/Rule
the agent evaluates NATIVELY, exactly the way domains/recognition_graph.py migrated
the recognition DECISION (Argmax over words of a Sum-over-Intersect score). This
module is now the I/O-boundary adapter for that Term, NOT a Python ranker.

THE CRITERION (the agent's, grounded in its compression drive):

  A capability that closes a gap UNIFIES every held postulate that derived it —
  closing it lets the agent re-express all of those postulates' consequences with
  one new mechanism instead of leaving each as a separate unrealized implication. So
  the COMPRESSION PAYOFF of a capability-axis = how many DISTINCT held postulates
  derive it (its foundational-ness in the agent's own order-N derivation graph). The
  more postulates one capability discharges, the more of the agent's knowledge it
  compresses — the MDL/curiosity selector the agent already uses, applied to its gap
  set. Tie-break: the SHALLOWER axis (smaller minimum derivation order) is the more
  direct, surer implication.

THE TERM (the agent's reasoning, evaluated by substrate.evaluate — the agent's
reality — NOT by Python):

    payoff(axis) = Count( Neighbours(axis, "unifies") )         # postulates unified
    score(axis)  = payoff(axis) * K  -  min_order(axis)         # tie-break folded in
    pick         = Argmax over the CapabilityAxis nodes of score(axis)

built from the agent's OWN DSL — Argmax / NodesWhere / Count / Neighbours / Times /
Minus / Attr — the same primitive family recognition_graph uses. K is large enough
(>> any order) that payoff strictly dominates and a shallower order only breaks ties
among equal payoff, so Argmax's first-encountered tie-rule never decides the pick.
A graph RULE evaluates this Term and writes the FrontierChoice node NATIVELY.

THE I/O-BOUNDARY ADAPTER (the permitted Python role — structural grouping, no
decision, the same kind of mechanical setup recognition_graph.mark_words does):
build_axis_env mints one CapabilityAxis node per capability signature the agent
synthesized and wires a `unifies` edge from it to each DISTINCT held postulate that
derived any of its gaps, and records the axis's minimum derivation order. Grouping
gap nodes by the capability they name and de-duplicating the postulates is a
mechanical world<->graph translation — there is NO conditional over graph state that
decides anything; the DECISION (which axis wins, by payoff*K - order) is the Term.

This closes the gap-PRIORITISER seam: the ranking is no longer Python arithmetic
over the gap graph (the previous version's honest caveat) — it is a Term the agent
owns and evaluates natively. See [[ozma_curiosity_drive]] / [[ozma_order_n_concepts]]
/ [[ozma_concepts_in_gamma]] / [[ozma_recognition_in_graph]].
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Graph-resident Term constructors (raw JSON wire form — identical encoding to
# substrate_rs Term.to_dict; the recognition_graph._Pred pattern). These BUILD
# the agent's reasoning as data; they make no decision.
# ---------------------------------------------------------------------------

AXIS_TYPE = "CapabilityAxis"      # one node per capability the agent synthesized
AXIS_FLAG = "is_axis"             # sentinel attr so NodesWhere can range over them
UNIFIES_EDGE = "unifies"          # axis -> each distinct held postulate it discharges
ORDER_ATTR = "min_order"          # the axis's shallowest derivation order (tie-break)
# K dominates the payoff term over the order tie-break: any plausible order (<100)
# is swamped, so higher payoff always wins and shallower order only breaks ties.
ORDER_K = 1000

# ---------------------------------------------------------------------------
# BUILT-BUT-INSUFFICIENT — the second gap SOURCE the meta-gap was missing.
#
# THE META-GAP (iter-42). order_n_postulates only synthesises ABSENT capabilities:
# an implication the agent has not yet built. A capability that IS built but is
# MEASURED below its target (a first-pass LPC / speaker-norm / coarticulation that
# underperforms) is read as CLOSED — the selector scores it on its compression
# payoff (postulates unified), which is irrelevant to "this built thing is the
# bottleneck", so the agent cannot prioritise its real frontier. The order-N
# DERIVATIVE knows the front-end is implicated (it derives those capabilities) but
# the bare RANKER scores them low because they are already built.
#
# THE FIX (the agent's OTHER frontier mechanism — the MEASUREMENT-YARDSTICK,
# generalised). perception_self_assessment already mints ONE generic perception/units
# axis from a yardstick shortfall; this generalises that to ANY built capability with
# a measured yardstick value below its target. A graph-resident Rule reads the
# agent's measurement Concepts (MeasuredCapability nodes the yardstick / do-contrast
# writes) and, for each built capability whose `measured` is below its `target`,
# RE-OPENS it as a CapabilityAxis carrying its SHORTFALL (target - measured). The
# ranking Term then adds a shortfall-weighted boost so that axis competes in the
# SAME Argmax — ranked by how far it underperforms, not by postulate-unification.
# No Python decision, no hardcoded capability list: the Rule consumes the measurement.
#
# The boost must dominate the compression payoff so a measured-insufficiency
# (payoff 0, no `unifies` edges) outranks the bare highest-foundationalness pick; a
# larger shortfall outranks a smaller one. SHORTFALL is in (0,1] for a normalised
# yardstick, so BOOST >> ORDER_K * (max plausible payoff) makes any positive
# shortfall dominate, and the shortfall magnitude orders the built-but-insufficient
# axes among themselves.
MEASURED_TYPE = "MeasuredCapability"   # a built cap's measured yardstick value + target
MEASURED_FLAG = "is_measured"          # sentinel so the synthesis Rule ranges over them
SHORTFALL_ATTR = "shortfall"           # target - measured (>0 = built-but-insufficient)
SATURATION_ATTR = "saturation"         # the agent's BELIEF in [0,1] that the capability
                                       # is SATURATED (its OWN measured yardstick met its
                                       # target); the DUAL of shortfall — discounts the
                                       # compression payoff so a done capability stops
                                       # winning by bare foundational-ness.
INSUFFICIENT_FLAG = "built_insufficient"  # 1 on an axis re-opened from a measured shortfall
# BOOST dominates payoff*K for any plausible payoff (a near-universal shape unifies
# < a few hundred postulates, so payoff*K < a few hundred-thousand); 10^9 swamps that
# while the shortfall (<=1) still orders insufficient axes among themselves at a scale
# far above the compression payoffs.
SHORTFALL_BOOST = 1_000_000_000

# ---------------------------------------------------------------------------
# Pipeline-level placement of an axis + the BELOW-FRONTIER guidance (the
# process-meta-assessor's signal wired INTO the ranker, not merely observed).
#
# The process_meta_assessor's BELOW_FRONTIER rule flags an iteration whose pick is
# DOWNSTREAM of the loop's current frontier. By itself that is observe-only: it sets
# a flag on a recorded Iteration node but cannot change the NEXT pick. To make the
# signal GUIDE the loop, the ranker must read the same comparison and discount
# below-frontier axes — the same graph-resident penalty pattern measurement_feedback
# uses for the exhaust signal. So each axis carries its pipeline LEVEL-RANK (where in
# the perception->recognition pipeline the capability sits), and the guided score
# subtracts a dominating penalty when that rank is downstream of the frontier rank
# the perception_self_assessment flag sets. The Argmax then re-picks AT the frontier.
LEVEL_RANK_ATTR = "level_rank"     # the axis's pipeline-level rank (smaller=upstream)
FRONTIER_ROOT_TYPE = "FrontierRoot"
FRONTIER_RANK_ATTR = "frontier_rank"   # live, set from perception_self_assessment
# The below-frontier penalty must dominate payoff*K so any below-frontier axis sinks
# below every at/above-frontier one (the redirect), exactly like the exhaust penalty.
BELOW_FRONTIER_PENALTY = ORDER_K * 1000

# Pipeline-level ranks (the agent's own upstream->downstream map; mirrors the
# process_meta_assessor seed's pipeline_levels). Smaller = more upstream (perception).
PIPELINE_LEVELS = {
    "perception_units": 1.0,
    "segmentation": 2.0,
    "speaker_normalization": 3.0,
    "feature_extraction": 4.0,
    "recognition": 5.0,
}
# Map a capability axis to its pipeline level by the capability terms-of-art it names.
# Mechanical lookup (no decision) — the same role _find_axis plays: translate the
# capability the gaps named into where in the pipeline that capability lives.
_KEY_TO_LEVEL = [
    # recognition / categorical-decision capabilities (downstream)
    (("cross-speaker-clustering", "unsupervised-clustering", "cross-speaker",
      "categor", "recogni", "classif", "lexical"), "recognition"),
    # sequence segmentation / chunking
    (("word-scale chunking", "transitional probability", "statistical segmentation",
      "n-gram boundary", "chunk", "boundary", "segment"), "segmentation"),
    # speaker / scale normalization
    (("speaker norm", "vocal-tract", "vtl", "ratio", "normaliz", "talker"),
     "speaker_normalization"),
    # front-end feature extraction (LPC/cepstral/all-pole) — a representation step
    (("all-pole", "levinson", "lpc-formant", "autoregressive", "cepstr",
      "parametric", "linear predict"), "feature_extraction"),
    # the units/perception front-end itself (cochlea, resolution, the raw units)
    (("cochlea", "resolution", "gammatone", "formant", "spectral peak",
      "acoustic", "unit", "perception"), "perception_units"),
]


def axis_pipeline_level(capability_keys) -> tuple[str, float]:
    """Map a CapabilityAxis to its pipeline LEVEL + rank by the capability terms it
    names. Mechanical world<->graph translation (no decision): returns
    (level_name, level_rank). Unmatched axes default to the most downstream rank so
    they are treated as below any frontier until placed (conservative)."""
    keys = [str(k).lower() for k in capability_keys]
    for needles, level in _KEY_TO_LEVEL:
        if any(any(n in k for k in keys) for n in needles):
            return level, PIPELINE_LEVELS[level]
    return "recognition", PIPELINE_LEVELS["recognition"]


class _Pred:
    """Thin carrier so substrate.evaluate(_Pred(term_json), env) runs the Term
    natively (same shim recognition_graph uses)."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nb(node, e): return {"type": "Neighbours", "node": node, "edge_type": e,
                          "any_type": False}
def _Count(src): return {"type": "Count", "source": src}
def _Times(items): return {"type": "Times", "items": list(items)}
def _Plus(items): return {"type": "Plus", "items": list(items)}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src,
                                    "var_name": var, "value": val, "default": None}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}


def payoff_term(axis_var: str = "x") -> dict:
    """payoff(axis) = Count(Neighbours(axis, "unifies")) — the number of DISTINCT
    held postulates the capability unifies, read straight off the agent's own
    derivation graph. A graph Term-tree (the agent's compression criterion)."""
    return _Count(_Nb(_V(axis_var), UNIFIES_EDGE))


def shortfall_boost_term(axis_var: str = "x",
                         boost: int = SHORTFALL_BOOST) -> dict:
    """shortfall(axis) * BOOST — the measurement-yardstick contribution to the score.
    For a normal (synthesised, never-measured) axis `shortfall` is 0 (the attr
    defaults to 0), so this is a no-op. For an axis RE-OPENED from a built-but-
    insufficient measurement, `shortfall` = target - measured > 0, and BOOST dominates
    the compression payoff so the Argmax prioritises the measured bottleneck; a larger
    shortfall outranks a smaller one. A graph Term-tree (Times / Attr) — the
    built-but-insufficient DECISION lives in the Term, not Python."""
    return _Times([_Attr(_V(axis_var), SHORTFALL_ATTR), _Lit(boost)])


def saturation_factor_term(axis_var: str = "x") -> dict:
    """(1 - saturation(axis)) — the agent's belief that the capability is SATURATED (its
    OWN measured yardstick met its target) DISCOUNTS its compression payoff. The DUAL of
    shortfall_boost: under-target BOOSTS (the live bottleneck), at/over-target SATURATES
    (downgrade). `saturation` defaults to 0 (the attr is absent / backfilled 0), so the
    factor is 1.0 and a never-measured / unsaturated axis ranks EXACTLY as before — the
    bare compression ranking is preserved. A graph Term-tree (Minus / Lit / Attr)."""
    return _Minus(_Lit(1.0), _Attr(_V(axis_var), SATURATION_ATTR))


def score_term(axis_var: str = "x", k: int = ORDER_K,
               boost: int = SHORTFALL_BOOST) -> dict:
    """score(axis) = payoff(axis) * K * (1 - saturation) - min_order(axis)
                     + shortfall(axis) * BOOST —
    compression payoff DISCOUNTED by the agent's saturation belief, with the shallower-
    order tie-break, PLUS the measurement-yardstick boost so a built-but-insufficient
    axis competes in the same Argmax. saturation defaults to 0 (factor 1.0) so a
    synthesised / never-measured axis ranks by the bare compression payoff; a capability
    the agent has measured to MEET its target gets saturation→1 → payoff→0 → it stops
    winning on foundational-ness and the next genuine frontier surfaces. The boost is 0
    for synthesised axes (shortfall defaults to 0). A graph Term-tree (Plus/Times/Minus).
    Saturation (over-target) and shortfall (under-target) are duals; both are read off
    the agent's own MeasuredCapability yardstick, never decided in Python."""
    return _Plus([_Minus(_Times([payoff_term(axis_var), _Lit(k),
                                 saturation_factor_term(axis_var)]),
                         _Attr(_V(axis_var), ORDER_ATTR)),
                  shortfall_boost_term(axis_var, boost)])


def pick_term(k: int = ORDER_K) -> dict:
    """pick = Argmax over the CapabilityAxis nodes of score(axis) — the whole
    gap-ranking DECISION, as a Term the agent owns and evaluates natively. Ranges
    over NodesWhere(CapabilityAxis, is_axis=1) so it sees exactly the axes the agent
    synthesized."""
    return _Argmax(_NodesWhere(AXIS_TYPE, AXIS_FLAG, _Lit(1.0)), "x",
                   score_term("x", k))


# ---------------------------------------------------------------------------
# The BELOW-FRONTIER guidance term — the assessor's signal, in the ranker.
# ---------------------------------------------------------------------------

def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _IfThenElse(cond, then, other): return {"type": "IfThenElse", "cond": cond,
                                            "then": then, "other": other}


def below_frontier_penalty_term(axis_var: str = "x", frontier_var: str = "F",
                                penalty: int = BELOW_FRONTIER_PENALTY) -> dict:
    """A dominating penalty for an axis DOWNSTREAM of the loop's live frontier rank,
    SCALED BY HOW FAR downstream it is — the process-meta-assessor's BELOW_FRONTIER
    comparison, evaluated by the RANKER so it CHANGES the pick instead of only flagging
    a past iteration.

      penalty(axis) = PENALTY * (level_rank - frontier_rank)   if level_rank > frontier
                    = 0                                          otherwise

    The DISTANCE scaling is what makes the redirect land MEANINGFULLY when no axis sits
    exactly at the frontier (the real case: the agent synthesizes no perception/units
    gap, only downstream representation/recognition gaps): the penalty dominates
    payoff*K, so the Argmax picks the axis CLOSEST to the frontier (smallest distance) —
    pulling the loop as far upstream toward the perception bottleneck as an available gap
    allows, rather than letting the high-payoff far-downstream recognition gap win. An
    at/above-frontier axis gets 0 (no-op). frontier_rank is read off the FrontierRoot,
    set live from perception_self_assessment. A graph Term-tree (Gt / IfThenElse / Times
    / Minus / Attr)."""
    lr = _Attr(_V(axis_var), LEVEL_RANK_ATTR)
    fr = _Attr(_V(frontier_var), FRONTIER_RANK_ATTR)
    downstream = _Gt(lr, fr)
    distance = _Minus(lr, fr)              # how far downstream of the frontier
    scaled = _Times([_Lit(penalty), distance])
    return _IfThenElse(downstream, scaled, _Lit(0))


def guided_score_term(axis_var: str = "x", frontier_var: str = "F",
                      k: int = ORDER_K,
                      penalty: int = BELOW_FRONTIER_PENALTY) -> dict:
    """score(axis) - below_frontier_penalty(axis, frontier) — the base compression
    score with the assessor's BELOW_FRONTIER discount folded in. Same scalar shape;
    a below-frontier axis sinks below every at/above-frontier one. A graph Term-tree."""
    return _Minus(score_term(axis_var, k),
                  below_frontier_penalty_term(axis_var, frontier_var, penalty))


def guided_pick_term(frontier_var: str = "F", k: int = ORDER_K,
                     penalty: int = BELOW_FRONTIER_PENALTY) -> dict:
    """pick = Argmax over the CapabilityAxis nodes of the GUIDED score — the ranking
    DECISION with the assessor's BELOW_FRONTIER guidance applied, as a Term the agent
    evaluates natively. The frontier rank is bound (var F) to the FrontierRoot."""
    return _Argmax(_NodesWhere(AXIS_TYPE, AXIS_FLAG, _Lit(1.0)), "x",
                   guided_score_term("x", frontier_var, k, penalty))


# ---------------------------------------------------------------------------
# I/O-boundary adapter — mechanical grouping/dedup of the agent's own gap nodes
# into CapabilityAxis nodes the Term can range over. No decision (the same kind of
# structural setup recognition_graph.mark_words does for the recognition Term).
# ---------------------------------------------------------------------------

def _axis_sig(capability_keys) -> frozenset:
    return frozenset(str(k).lower() for k in capability_keys)


# Specificity gate: the fraction of the postulate corpus a shape may fire on before
# its "unifications" stop counting. A shape that fires on >PROMISCUITY_FRAC of all
# postulates is, by MDL, a near-universal predicate carrying ~0 bits of distinction —
# it cannot perform a genuine compression/unification (it groups unrelated postulates
# under one bland canned consequence). This is the SCALED-machinery failure the
# rule-walker harvest (7→503 shapes) introduced: shapes whose match_patterns are bare
# common words ('\\bruns\\b', '\\bsubstrate\\b') fire on ~50% of postulates and the
# payoff = count(distinct postulates unified) rewards exactly that promiscuity, so the
# Argmax pick lands on the most content-free gap. Gating those firings out makes the
# agent's EXISTING payoff Term (Count of `unifies` edges) specificity-correct without a
# new term — the same Argmax just stops over-counting artifacts.
PROMISCUITY_FRAC = 0.10


def shape_firing_breadth(substrate, shape_lib) -> dict:
    """For each implication-shape, how many of the agent's held postulates its
    match_patterns fire on — the shape's FIRING BREADTH over the corpus. A purely
    structural measurement of the catalog (no decision): the same regex match
    differentiate() runs, counted across the postulate texts. Returns
    {shape_name: n_postulates_it_fires_on}. The via_shape labels recorded on gaps
    use the bare shape name, so the keys here match those labels directly."""
    import re
    from .order_n_postulates import harvest_postulates
    texts = [(t or "").lower() for _, _, t in harvest_postulates(substrate)]
    breadth = {}
    for sh in shape_lib:
        pats = sh.get("match_patterns", [])
        # Honour the shape's match_mode so the breadth measured here matches
        # what differentiate() actually fires on: rule-derived shapes use
        # 'all' (the antecedent conjunction must co-occur), the regex-extractor
        # kinds use 'any'. Measuring with the wrong combiner would over-report
        # rule-derived breadth and reintroduce the artifact the harvest fix
        # removed at the source.
        if sh.get("match_mode") == "all":
            breadth[sh["name"]] = sum(
                1 for t in texts if pats and all(re.search(p, t) for p in pats))
        else:
            breadth[sh["name"]] = sum(
                1 for t in texts if any(re.search(p, t) for p in pats))
    return breadth


def build_axis_env(substrate, shape_breadth: dict | None = None) -> list:
    """Translate the agent's recorded SynthesizedGap nodes into CapabilityAxis nodes
    the ranking Term ranges over. Mechanical world<->graph structuring only:

      • one CapabilityAxis per capability signature (the capability the gaps name);
      • a `unifies` edge from each axis to every DISTINCT held postulate Concept that
        derived any of its gaps (read off each gap's own `derived_from` edge);
      • `min_order` = the shallowest derivation order among the axis's gaps.

    De-duplicating the postulates is a structural translation, NOT a decision — it
    builds the graph the Term reads, exactly the role a world adapter plays. Idempotent
    (skips axes already built). Returns the list of CapabilityAxis node ids.

    `shape_breadth` (optional): a {shape_name: n_postulates_it_fires_on} map (from
    shape_firing_breadth). When supplied, a gap's contribution to its axis is GATED by
    the specificity of the shape(s) that produced it — a firing whose ONLY producing
    shape is promiscuous (fires on > PROMISCUITY_FRAC of the corpus) does not wire a
    `unifies` edge, because a near-universal predicate cannot perform a genuine
    unification. This makes the existing payoff Term (Count of `unifies` edges)
    specificity-correct on the SCALED gap-set. Default None keeps the prior behaviour
    (no gate) so existing callers/tests are unchanged."""
    # admissible edge: axis -> postulate Concept (mirrors order_n's derived_from prod).
    try:
        substrate.add_production({
            "src": {"type": AXIS_TYPE, "var": "a"},
            "edge_type": UNIFIES_EDGE,
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "gap_prioritiser:unifies"})
    except Exception:
        pass

    # Backfill on EVERY is_axis node (not only the SynthesizedGap-grouped ones below):
    # axes minted directly by a Rule (the built-but-insufficient synthesis, the
    # perception-units synthesis, the measurement blocker) carry capability_keys but
    # may lack pipeline level_rank or a numeric shortfall. Set them so the ranking +
    # guidance Terms always read numbers. Mechanical, idempotent — no decision.
    for ax in substrate.nodes(AXIS_TYPE):
        aa = substrate.node(ax)["attrs"]
        if aa.get(AXIS_FLAG) != 1.0:
            continue
        if aa.get(LEVEL_RANK_ATTR) is None:
            lvl, rnk = axis_pipeline_level(aa.get("capability_keys", []))
            substrate.set_attr(ax, "pipeline_level", lvl)
            substrate.set_attr(ax, LEVEL_RANK_ATTR, float(rnk))
        if aa.get(SHORTFALL_ATTR) is None:
            substrate.set_attr(ax, SHORTFALL_ATTR, 0.0)
        if aa.get(SATURATION_ATTR) is None:
            substrate.set_attr(ax, SATURATION_ATTR, 0.0)
        if aa.get("attempted_marginal") is None:
            substrate.set_attr(ax, "attempted_marginal", 0.0)
        if aa.get(ORDER_ATTR) is None:
            substrate.set_attr(ax, ORDER_ATTR, 1.0)
    _wire_saturation(substrate)   # the agent's saturation belief from its OWN yardstick

    n_post = None
    if shape_breadth is not None:
        try:
            from .order_n_postulates import harvest_postulates
            n_post = len(harvest_postulates(substrate))
        except Exception:
            n_post = None
    promisc_cap = (n_post * PROMISCUITY_FRAC) if n_post else None

    existing = {frozenset(substrate.node(n)["attrs"].get("axis_sig") or [])
                for n in substrate.nodes(AXIS_TYPE)}

    groups: dict[frozenset, dict] = {}
    for nid in substrate.nodes("SynthesizedGap"):
        a = substrate.node(nid)["attrs"]
        keys = list(a.get("capability_keys", []))
        if not keys:
            continue
        # Specificity gate: keep this firing only if at least one producing shape is
        # SPECIFIC enough (fires on <= promisc_cap postulates). A gap whose every
        # via_shape is promiscuous is a regex collision, not a unification — drop it.
        if promisc_cap is not None:
            vias = list(a.get("via_shapes", []))
            specific = [v for v in vias
                        if shape_breadth.get(v, 0) <= promisc_cap]
            if vias and not specific:
                continue
        sig = _axis_sig(keys)
        g = groups.setdefault(sig, {
            "capability_keys": keys,
            "postulates": {},          # postulate name -> its Concept node id
            "orders": [],
            "gap_text": str(a.get("gap", "")),
            "source_domains": set(),
            "source_concepts": set(),
        })
        # the postulate this gap derives from, as the actual Concept node(s) on its
        # own derived_from edge (dedup by name -> distinct postulates only).
        post_name = a.get("from_postulate")
        for p in substrate.neighbours(nid, "derived_from"):
            pn = substrate.node(p)["attrs"].get("name", post_name)
            g["postulates"][str(pn)] = p
        try:
            g["orders"].append(int(a.get("order", 99)))
        except (TypeError, ValueError):
            pass
        g["source_domains"].update(str(d) for d in a.get("source_domains", []))
        g["source_concepts"].update(str(c) for c in a.get("source_concepts", []))

    axis_ids = []
    for sig, g in groups.items():
        if sig in existing:
            ex = next(
                n for n in substrate.nodes(AXIS_TYPE)
                if frozenset(substrate.node(n)["attrs"].get("axis_sig") or []) == sig)
            # backfill the pipeline level-rank on axes minted before this wiring
            # existed (e.g. measurement-derived blockers) so the guidance term's Attr
            # read is always a number. Mechanical, idempotent.
            if substrate.node(ex)["attrs"].get(LEVEL_RANK_ATTR) is None:
                lvl, rnk = axis_pipeline_level(
                    substrate.node(ex)["attrs"].get("capability_keys", []))
                substrate.set_attr(ex, "pipeline_level", lvl)
                substrate.set_attr(ex, LEVEL_RANK_ATTR, float(rnk))
            # backfill shortfall=0 on axes minted before the built-but-insufficient
            # wiring existed, so the score Term's shortfall Attr read is always a number.
            if substrate.node(ex)["attrs"].get(SHORTFALL_ATTR) is None:
                substrate.set_attr(ex, SHORTFALL_ATTR, 0.0)
            axis_ids.append(ex)
            continue
        level_name, level_rank = axis_pipeline_level(g["capability_keys"])
        ax = substrate.add_node(AXIS_TYPE, {
            AXIS_FLAG: 1.0,
            "axis_sig": sorted(sig),
            "capability_keys": list(g["capability_keys"]),
            # pipeline placement so the BELOW_FRONTIER guidance term can compare this
            # axis's rank to the live frontier rank (mechanical map, no decision).
            "pipeline_level": level_name,
            LEVEL_RANK_ATTR: float(level_rank),
            # 0 until a measurement marks this axis attempted-and-exhausted (the
            # move-on signal measurement_feedback writes); seeded so the ranking
            # Term's Attr read is always a number, never None.
            "attempted_marginal": 0.0,
            # 0 for a synthesised (never-measured) axis, so the score Term's
            # shortfall-boost is a no-op for it; a built-but-insufficient axis carries
            # a positive shortfall (target - measured), set by the synthesis Rule.
            SHORTFALL_ATTR: 0.0,
            ORDER_ATTR: float(min(g["orders"]) if g["orders"] else 99),
            "gap_text": g["gap_text"],
            "source_domains": sorted(g["source_domains"]),
            "source_concepts": sorted(g["source_concepts"]),
            "origin": "gap_prioritiser",
            "composed_by": "agent",
        })
        for pid in g["postulates"].values():
            try:
                substrate.add_edge(ax, UNIFIES_EDGE, pid, {})
            except Exception:
                pass
        axis_ids.append(ax)
    # Include axes minted DIRECTLY by a Rule (built-but-insufficient re-opens, the
    # perception-units synthesis, measurement blockers) — they carry no SynthesizedGap
    # so the grouping above never lists them, but they are real is_axis nodes the
    # ranker must see. The early backfill pass already gave them level_rank/shortfall.
    seen_ids = set(axis_ids)
    for ax in substrate.nodes(AXIS_TYPE):
        if (ax not in seen_ids
                and substrate.node(ax)["attrs"].get(AXIS_FLAG) == 1.0):
            axis_ids.append(ax)
    return axis_ids


# ---------------------------------------------------------------------------
# BUILT-BUT-INSUFFICIENT — re-open a built capability measured below its target.
#
# The I/O adapter (record_measured_capability) translates the agent's OWN yardstick
# / do-contrast result into a MeasuredCapability node (the measured value + the
# target it set). The graph Rule (synthesise_builtinsufficient_gap) does the DECISION
# natively: for each MeasuredCapability whose `measured` is below its `target`, mint a
# CapabilityAxis for that SAME capability carrying its `shortfall` = target - measured,
# so the existing ranking Argmax (whose score now includes shortfall*BOOST) re-picks
# it. No Python decides "is this built thing the frontier?" — the Rule + the score
# Term do, reading the measurement.
# ---------------------------------------------------------------------------

def _wire_saturation(substrate) -> None:
    """The agent's SATURATION belief, derived from its OWN yardstick (the dual of the
    shortfall wiring): for each MeasuredCapability, saturation = clamp(measured/target,
    0, 1) on the CapabilityAxis sharing its capability signature. measured >= target ->
    saturation 1 -> payoff fully discounted (the capability is DONE, stop ranking it by
    bare foundational-ness); under target the shortfall BOOST dominates so the partial
    saturation is moot. Pure graph<->graph I/O — reads the measurement node, writes the
    belief attr; the DECISION stays the score Term. Idempotent."""
    sat_by_sig: dict = {}
    for n in substrate.nodes(MEASURED_TYPE):
        a = substrate.node(n)["attrs"]
        sig = frozenset(a.get("cap_sig", []) or _axis_sig(a.get("capability_keys", [])))
        tgt = float(a.get("target", 0.0) or 0.0)
        m = float(a.get("measured", 0.0) or 0.0)
        sat = 0.0 if tgt <= 0 else max(0.0, min(1.0, m / tgt))
        if sig:
            sat_by_sig[sig] = max(sat_by_sig.get(sig, 0.0), sat)
    if not sat_by_sig:
        return
    for ax in substrate.nodes(AXIS_TYPE):
        aa = substrate.node(ax)["attrs"]
        if aa.get(AXIS_FLAG) != 1.0:
            continue
        axsig = frozenset(_axis_sig(aa.get("capability_keys", [])))
        best = max((s for sig, s in sat_by_sig.items() if sig & axsig), default=None)
        if best is not None:
            substrate.set_attr(ax, SATURATION_ATTR, float(best))


def mark_saturated(substrate, capability_keys, saturation: float = 1.0) -> int:
    """Set the agent's SATURATION belief directly on the matching CapabilityAxis — for a
    capability the agent believes done without a numeric yardstick (the explicit dual of
    re-opening an insufficient axis). Returns the number of axes marked."""
    sig = frozenset(_axis_sig(capability_keys))
    n = 0
    for ax in substrate.nodes(AXIS_TYPE):
        aa = substrate.node(ax)["attrs"]
        if aa.get(AXIS_FLAG) == 1.0 and frozenset(
                _axis_sig(aa.get("capability_keys", []))) & sig:
            substrate.set_attr(ax, SATURATION_ATTR, float(saturation))
            n += 1
    return n


def record_measured_capability(substrate, capability_keys, *, measured: float,
                               target: float, metric: str = "",
                               note: str = "", fresh: bool = False) -> object:
    """Translate the agent's yardstick / do-contrast result for a BUILT capability
    into graph state the synthesis Rule reads: a MeasuredCapability node carrying the
    capability it names, its MEASURED yardstick value, and the TARGET the agent set
    for it. Pure world<->graph I/O — the probe computed the numbers; this only writes
    them as a node (no decision: whether measured < target is the Rule's call). The
    capability_keys are the SAME terms-of-art the order-N synthesis / axis map use, so
    a re-opened axis maps to the right pipeline level. Idempotent on the capability
    signature: updates the latest reading in place. Returns the node id.

    `fresh=True` (the investigation path, the agent's throughput fix ask_jabberwock_throughput):
    ALWAYS mint a NEW node, never upsert. The re-mint loop banks each trial once via a `banked`
    marker edge on the measurement node; upserting re-uses ONE node across trials and re-stamps it,
    so bank re-fired ~9x on the same node (2 nodes / 18 banks) and investigated_count was meaningless.
    A fresh node per trial = one genuine measurement per trial = banked exactly once."""
    sig = sorted(_axis_sig(capability_keys))
    existing = None
    if not fresh:
        for n in substrate.nodes(MEASURED_TYPE):
            if sorted(substrate.node(n)["attrs"].get("cap_sig", [])) == sig:
                existing = n
                break
    if existing is not None:
        substrate.set_attr(existing, "measured", float(measured))
        substrate.set_attr(existing, "target", float(target))
        substrate.set_attr(existing, "synth_pending", 1)
        if metric:
            substrate.set_attr(existing, "metric", str(metric))
        if note:
            substrate.set_attr(existing, "note", str(note))
        return existing
    return substrate.add_node(MEASURED_TYPE, {
        MEASURED_FLAG: 1.0,
        "cap_sig": sig,
        "capability_keys": list(capability_keys),
        "measured": float(measured),
        "target": float(target),
        "metric": str(metric),
        "note": str(note),
        # armed so the synthesis Rule evaluates this reading once; the Rule clears it.
        "synth_pending": 1,
        "origin": "gap_prioritiser:measured_capability",
        "composed_by": "world_adapter",
    })


def install_builtinsufficient_gap_rule(substrate) -> dict:
    """Install the built-but-insufficient SYNTHESIS as a graph-resident Rule. For each
    MeasuredCapability whose `measured` is below its `target` (and a synthesis is
    pending), mint a CapabilityAxis re-opening that capability as a gap, carrying
    `shortfall` = target - measured computed NATIVELY in the effect, flagged is_axis so
    the ranker ranges over it, and a `re_opens` provenance edge from the measurement to
    the axis. A capability measured AT/ABOVE its target mints NO axis (the IfThenElse
    yields shortfall 0 and the gate `where` requires measured < target). The DECISION
    (re-open iff built-but-insufficient, weight by the shortfall) is the Rule + the
    score Term, not Python. Returns {'rule_index'}.

    NB the minted axis carries NO capability_keys-derived level here (the add_node
    effect cannot run the Python level map); build_axis_env backfills its pipeline
    level_rank + a 0-default on un-set attrs on the next env build, so the guided
    ranker can place it. Its OWN payoff is 0 (no `unifies` edges) — correct: it wins by
    the measured shortfall, not by postulate unification."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    # admissible edges: measurement -> axis (provenance), self-marker to bind M.
    for et, tt in (("re_opens", AXIS_TYPE), ("mc_self", MEASURED_TYPE)):
        try:
            substrate.add_production({
                "src": {"type": MEASURED_TYPE, "var": "a"},
                "edge_type": et, "tgt": {"type": tt, "var": "b"},
                "provenance": f"gap_prioritiser:{et}"})
        except Exception:
            pass
    for m in substrate.nodes(MEASURED_TYPE):
        try:
            substrate.add_edge(m, "mc_self", m, {})
        except Exception:
            pass
    M = _V("M")
    below = _Gt(_Attr(M, "target"), _Attr(M, "measured"))   # measured < target
    shortfall = _Minus(_Attr(M, "target"), _Attr(M, "measured"))
    rule = {
        "name": "synthesise_builtinsufficient_gap",
        "match": [["M", "mc_self", "M"]],
        # fire only on a built-but-insufficient reading with a pending synthesis.
        "where": {"type": "And", "items": (
            below,
            {"type": "Eq", "a": _Attr(M, "synth_pending"), "b": _Lit(1)})},
        "effects": [
            ["add_node", "A", AXIS_TYPE, {
                AXIS_FLAG: 1.0,
                INSUFFICIENT_FLAG: 1.0,
                # the measured shortfall (target - measured), computed natively — this
                # is what the score Term's shortfall-boost ranks the axis by.
                SHORTFALL_ATTR: {"__term__": shortfall},
                "measured": {"__term__": _Attr(M, "measured")},
                "target": {"__term__": _Attr(M, "target")},
                "min_order": 1.0,
                "attempted_marginal": 0.0,
                # axis_sig = the measurement's cap_sig, so build_axis_env's dedup keys
                # the re-opened axis the same way it keys synthesised axes (idempotent).
                "axis_sig": {"__term__": _Attr(M, "cap_sig")},
                "cap_sig": {"__term__": _Attr(M, "cap_sig")},
                "capability_keys": {"__term__": _Attr(M, "capability_keys")},
                "gap_text": ("built-but-insufficient: this capability is implemented "
                             "but measured below its target by the yardstick; "
                             "re-opened as a gap ranked by the shortfall"),
                "origin": "gap_prioritiser:built_insufficient",
                "provenance": "synthesised_from_measured_shortfall",
                "composed_by": "agent",
            }],
            ["add_edge", "M", "re_opens", "A", {}],
            ["set_attr", "M", "synth_pending", 0],
        ],
    }
    return {"rule_index": nat.add_rule(rule)}


def synthesise_builtinsufficient_gaps(substrate, max_iters: int = 64) -> list:
    """Fire the built-but-insufficient synthesis Rule until no MeasuredCapability has a
    pending synthesis, then return the re-opened axis ids. The DECISION is the Rule's;
    Python only installs + fires it + reads back. Idempotent: a capability measured
    at/above target mints nothing; one measured below target mints exactly one axis per
    fresh reading. After firing, runs build_axis_env so the new axes get their pipeline
    level_rank + default attrs backfilled for the (guided) ranker."""
    info = install_builtinsufficient_gap_rule(substrate)
    before = set(substrate.nodes(AXIS_TYPE))

    def _pending():
        return [m for m in substrate.nodes(MEASURED_TYPE)
                if substrate.node(m)["attrs"].get("synth_pending") == 1]
    for _ in range(max_iters):
        if not _pending():
            break
        nat = substrate._inner if hasattr(substrate, "_inner") else substrate
        nat.apply_rule_once(info["rule_index"])
    minted = [n for n in substrate.nodes(AXIS_TYPE) if n not in before]
    # backfill pipeline level_rank + 0-default attrs on the freshly-minted axes.
    build_axis_env(substrate)
    return minted


# ---------------------------------------------------------------------------
# The PICK — a graph Rule evaluates the ranking Term and writes the choice
# natively. The decision logic is in the Term, not Python.
# ---------------------------------------------------------------------------

def rank_gaps(substrate, k: int = ORDER_K,
              shape_breadth: dict | None = None) -> list[dict]:
    """The agent's ranking, computed by EVALUATING the payoff/score Terms natively
    over each CapabilityAxis (substrate.evaluate — the agent's reality), best first.
    Builds the axis env first (mechanical) if it is not yet present. The numbers come
    out of the graph Term, not Python arithmetic. Returns dicts:
      {capability_keys, payoff, min_order, score, source_domains, source_concepts,
       gap_text, axis_id}.

    `shape_breadth`: passed through to build_axis_env — when supplied, the specificity
    gate keeps the payoff Term from over-counting promiscuous-shape firings."""
    build_axis_env(substrate, shape_breadth=shape_breadth)
    rows = []
    for ax in substrate.nodes(AXIS_TYPE):
        if substrate.node(ax)["attrs"].get(AXIS_FLAG) != 1.0:
            continue
        a = substrate.node(ax)["attrs"]
        payoff = substrate.evaluate(_Pred(payoff_term("x")), {"x": ax})
        score = substrate.evaluate(_Pred(score_term("x", k)), {"x": ax})
        rows.append({
            "capability_keys": list(a.get("capability_keys", [])),
            "payoff": int(payoff),
            "min_order": int(a.get(ORDER_ATTR, 99)),
            "score": int(score),
            "source_domains": list(a.get("source_domains", [])),
            "source_concepts": list(a.get("source_concepts", [])),
            "gap_text": a.get("gap_text", ""),
            "axis_id": ax,
        })
    rows.sort(key=lambda r: -r["score"])
    return rows


def install_pick_rule(substrate, k: int = ORDER_K) -> dict:
    """Install the PICK as a graph-resident Rule: it evaluates the ranking Term
    (Argmax over the CapabilityAxis nodes of payoff*K - order) and writes the winner
    onto a FrontierRoot node natively — the agent enacting its own choice, no Python
    decision. Returns {'root','rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = next((n for n in substrate.nodes("FrontierRoot")), None)
    if root is None:
        root = substrate.add_node("FrontierRoot",
                                  {"origin": "gap_prioritiser", "pick_pending": 1})
    else:
        substrate.set_attr(root, "pick_pending", 1)
    # The Rule binds R to the FrontierRoot (matched by its self-edge marker) and
    # sets `picked_axis` to the Argmax Term's value — the chosen CapabilityAxis node.
    try:
        substrate.add_production({
            "src": {"type": "FrontierRoot", "var": "a"},
            "edge_type": "self",
            "tgt": {"type": "FrontierRoot", "var": "b"},
            "provenance": "gap_prioritiser:self"})
        substrate.add_edge(root, "self", root, {})
    except Exception:
        pass
    rule = {
        "name": "pick_frontier_gap",
        "match": [["R", "self", "R"]],
        "where": _Lit(True),
        "effects": [
            ["set_attr", "R", "picked_axis", {"__term__": pick_term(k)}],
            ["set_attr", "R", "pick_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def pick_frontier(substrate, k: int = ORDER_K,
                  shape_breadth: dict | None = None) -> dict | None:
    """The agent's PICK, ENACTED in the graph: build the axis env (mechanical),
    install + fire the graph Rule whose effect evaluates the ranking Term natively,
    read back the winning CapabilityAxis the agent chose, and record it as a
    FrontierChoice node. Returns the winning gap dict (with criterion + runner-up for
    an honest margin), or None if no gaps exist.

    The DECISION is the Term the Rule evaluates — Python here only builds the env,
    fires the Rule, and reads the result back out (the permitted I/O role).

    `shape_breadth`: passed to build_axis_env to apply the specificity gate (drop
    promiscuous-shape firings so the payoff Term ranks genuine unifications)."""
    axes = build_axis_env(substrate, shape_breadth=shape_breadth)
    if not axes:
        return None
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    info = install_pick_rule(substrate, k)
    root = info["root"]
    for _ in range(8):
        if substrate.node(root)["attrs"].get("pick_pending") != 1:
            break
        nat.apply_rule_once(info["rule_index"])
    picked = substrate.node(root)["attrs"].get("picked_axis")
    if picked is None:
        return None

    ranked = rank_gaps(substrate, k, shape_breadth=shape_breadth)  # native Term values
    win_row = next((r for r in ranked if r["axis_id"] == picked), ranked[0])
    runner = next((r for r in ranked if r["axis_id"] != picked), None)
    winner = dict(win_row)
    winner["postulates_unified"] = winner["payoff"]
    winner["criterion"] = ("compression payoff = number of held postulates the "
                           "capability unifies (Count of `unifies` edges in the "
                           "graph); tie-break shallower order; pick = Argmax over "
                           "CapabilityAxis of payoff*K - order — a graph Term-tree")
    winner["runner_up_payoff"] = runner["payoff"] if runner else 0
    try:
        substrate.add_node("FrontierChoice", {
            "origin": "gap_prioritiser",
            "criterion": winner["criterion"],
            "capability_keys": list(winner["capability_keys"]),
            "payoff": winner["payoff"],
            "min_order": winner["min_order"],
            "score": winner["score"],
            "picked_axis": picked,
            "composed_by": "agent",
            "decision_in": "graph_term",
        })
    except Exception:
        pass
    return winner


# ---------------------------------------------------------------------------
# The GUIDED pick — the assessor's BELOW_FRONTIER signal CHANGES the pick.
# ---------------------------------------------------------------------------

def set_frontier_rank(substrate, frontier_rank: float, frontier_level: str = "") -> object:
    """Write the loop's LIVE frontier rank onto the FrontierRoot so the guided ranking
    Term reads it (the auto-wire point: in the live loop this comes straight from
    perception_self_assessment's frontier flag, NOT a constant). Mechanical I/O."""
    root = next((n for n in substrate.nodes(FRONTIER_ROOT_TYPE)), None)
    if root is None:
        root = substrate.add_node(FRONTIER_ROOT_TYPE,
                                  {"origin": "gap_prioritiser", "pick_pending": 1})
    substrate.set_attr(root, FRONTIER_RANK_ATTR, float(frontier_rank))
    if frontier_level:
        substrate.set_attr(root, "frontier_level", str(frontier_level))
    return root


def rank_with_guidance(substrate, frontier_rank: float, k: int = ORDER_K,
                       penalty: int = BELOW_FRONTIER_PENALTY,
                       shape_breadth: dict | None = None) -> list[dict]:
    """Rank every axis by the GUIDED score (base score minus the below-frontier
    penalty), evaluated NATIVELY against the live frontier rank, best first. Reports
    base score, level_rank, below_frontier flag, and guided score per axis so the
    redirect is auditable. Numbers come out of the graph Term."""
    build_axis_env(substrate, shape_breadth=shape_breadth)
    froot = set_frontier_rank(substrate, frontier_rank)
    rows = []
    for ax in substrate.nodes(AXIS_TYPE):
        if substrate.node(ax)["attrs"].get(AXIS_FLAG) != 1.0:
            continue
        a = substrate.node(ax)["attrs"]
        env = {"x": ax, "F": froot}
        base = int(substrate.evaluate(_Pred(score_term("x", k)), env))
        pen = int(substrate.evaluate(
            _Pred(below_frontier_penalty_term("x", "F", penalty)), env))
        guided = int(substrate.evaluate(
            _Pred(guided_score_term("x", "F", k, penalty)), env))
        rows.append({
            "capability_keys": list(a.get("capability_keys", [])),
            "payoff": int(substrate.evaluate(_Pred(payoff_term("x")), env)),
            "pipeline_level": a.get("pipeline_level"),
            "level_rank": int(a.get(LEVEL_RANK_ATTR, 99)),
            "base_score": base,
            "below_frontier": 1 if pen > 0 else 0,
            "guided_score": guided,
            "axis_id": ax,
        })
    rows.sort(key=lambda r: -r["guided_score"])
    return rows


def pick_with_guidance(substrate, frontier_rank: float, k: int = ORDER_K,
                       penalty: int = BELOW_FRONTIER_PENALTY,
                       shape_breadth: dict | None = None) -> dict | None:
    """Enact the GUIDED pick in the graph: build the axis env, write the live frontier
    rank onto the FrontierRoot, install + fire a Rule whose effect evaluates the GUIDED
    Argmax Term natively (binding F to the FrontierRoot), read back the chosen axis.
    The assessor's BELOW_FRONTIER signal is now IN the pick: a below-frontier axis is
    penalised below every at/above-frontier one, so the Argmax re-picks at the frontier.
    Returns the winning gap dict (with the ungated/un-guided pick for the contrast), or
    None if no axes. The DECISION is the Term; Python only fires it + reads back."""
    build_axis_env(substrate, shape_breadth=shape_breadth)
    axes = [n for n in substrate.nodes(AXIS_TYPE)
            if substrate.node(n)["attrs"].get(AXIS_FLAG) == 1.0]
    if not axes:
        return None
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    froot = set_frontier_rank(substrate, frontier_rank)
    substrate.set_attr(froot, "pick_pending", 1)
    try:
        substrate.add_production({
            "src": {"type": FRONTIER_ROOT_TYPE, "var": "a"}, "edge_type": "self",
            "tgt": {"type": FRONTIER_ROOT_TYPE, "var": "b"},
            "provenance": "gap_prioritiser:self"})
        substrate.add_edge(froot, "self", froot, {})
    except Exception:
        pass
    rule = {
        "name": "pick_frontier_gap_guided",
        "match": [["F", "self", "F"]],
        "where": _Lit(True),
        "effects": [
            ["set_attr", "F", "picked_axis",
             {"__term__": guided_pick_term("F", k, penalty)}],
            ["set_attr", "F", "pick_pending", 0],
        ],
    }
    ri = nat.add_rule(rule)
    for _ in range(8):
        if substrate.node(froot)["attrs"].get("pick_pending") != 1:
            break
        nat.apply_rule_once(ri)
    picked = substrate.node(froot)["attrs"].get("picked_axis")
    if picked is None:
        return None
    guided_rows = rank_with_guidance(substrate, frontier_rank, k, penalty,
                                     shape_breadth=shape_breadth)
    base_rows = rank_gaps(substrate, k, shape_breadth=shape_breadth)
    win = next((r for r in guided_rows if r["axis_id"] == picked), guided_rows[0])
    ungated = base_rows[0] if base_rows else None
    out = dict(win)
    out["criterion"] = ("compression payoff*K - order - BELOW_FRONTIER penalty "
                        "(pipeline level_rank > live frontier_rank); pick = Argmax "
                        "over CapabilityAxis of the guided score — a graph Term-tree "
                        "with the process-meta-assessor's signal folded into the rank")
    out["frontier_rank"] = frontier_rank
    out["unguided_pick_keys"] = (list(ungated["capability_keys"]) if ungated else [])
    out["unguided_pick_level"] = (
        axis_pipeline_level(ungated["capability_keys"])[0] if ungated else "")
    out["pick_changed"] = (out["axis_id"] != ungated["axis_id"]) if ungated else False
    try:
        substrate.add_node("FrontierChoice", {
            "origin": "gap_prioritiser:guided",
            "criterion": out["criterion"],
            "capability_keys": list(out["capability_keys"]),
            "pipeline_level": out.get("pipeline_level"),
            "guided_score": out["guided_score"],
            "frontier_rank": frontier_rank,
            "picked_axis": picked,
            "unguided_pick": out["unguided_pick_keys"],
            "pick_changed": out["pick_changed"],
            "composed_by": "agent",
            "decision_in": "graph_term",
        })
    except Exception:
        pass
    return out


__all__ = ["payoff_term", "score_term", "shortfall_boost_term", "pick_term",
           "build_axis_env", "rank_gaps", "install_pick_rule", "pick_frontier",
           "shape_firing_breadth", "PROMISCUITY_FRAC",
           "below_frontier_penalty_term", "guided_score_term", "guided_pick_term",
           "set_frontier_rank", "rank_with_guidance", "pick_with_guidance",
           "axis_pipeline_level", "PIPELINE_LEVELS", "LEVEL_RANK_ATTR",
           "FRONTIER_RANK_ATTR", "AXIS_TYPE", "UNIFIES_EDGE",
           "record_measured_capability", "install_builtinsufficient_gap_rule",
           "synthesise_builtinsufficient_gaps", "MEASURED_TYPE", "MEASURED_FLAG",
           "SHORTFALL_ATTR", "INSUFFICIENT_FLAG", "SHORTFALL_BOOST"]

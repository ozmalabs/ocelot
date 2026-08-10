"""order_n_postulates — the agent SYNTHESIZES its own gaps.

The meta-ability this module gives the agent is to DERIVE its next capability
ITSELF, rather than surface only gaps a human (or a seeded rule's conclusion)
already wrote down. It does this by LIFTING the agent's existing order-N operator
(domains/order_n_concepts.py — the recursive finite difference over a SIGNAL
dimension: 0=value, 1=tilt, 2=curvature) from signals to KNOWLEDGE:

  • order-0  = a postulate the agent HOLDS — a science Concept / fact (a graph node).
  • order-1  = the DERIVATIVE of that postulate = what it IMPLIES but the agent has
               NOT yet realized (postulated or implemented).
  • order-2  = implications of implications.   …   order-N.
  • a GAP    = an order-k implication that is NOT already a held postulate or an
               implemented element AND that coheres / compresses (it follows + it
               unifies). Compression is the selector — never a search.

The DERIVATIVE step (order k -> k+1) is the agent's OWN move, not an opaque oracle.
It is the analogical-transfer mechanism (domains/analogy.py) lifted to knowledge:
abstract the STRUCTURAL PROPERTY a postulate asserts about its object (e.g. "the
vocal tract is a LINEAR FILTER"), then transfer an implication-SHAPE the agent
already holds SOMEWHERE in its breadth (linear-algebra / signals / physics: "a
linear operator is invertible", "a linear time-invariant system has an all-pole /
parametric model") onto that object. The transferred consequence is the order-1
postulate. Re-applying gives order-2, and so on.

  worked example (the test):
    order-0  "the vocal tract is a LINEAR FILTER"   (held: source_filter_theory)
       │  structural property: <object> is a linear filter
       ▼  transfer implication-shape  "a linear filter is invertible/deconvolvable"
    order-1  "a linear filter is invertible — the filter can be DECONVOLVED out"
       │  structural property: <object> is invertible / parametrically identifiable
       ▼  transfer implication-shape  "an invertible LTI filter has an all-pole model"
    order-2  "an all-pole (LPC) model identifies a linear filter's resonances"
       ▼  SELECTOR: is "LPC extraction" a held postulate / implemented element? NO.
    GAP      LPC-based formant extraction — DERIVED from the agent's own postulate,
             with no seeded rule naming it and no human pointing at it.

A peer LLM MAY help ARTICULATE candidate implications in the agent's grounded
vocabulary, but it is never the driver: the order-N STRUCTURE proposes WHICH
postulate to differentiate and the SELECTOR decides which implications are real
gaps. The operator is re-runnable over ANY postulate (run() takes a postulate
name); generality, not a hand-fit to LPC, is the point.

Output: each synthesized gap is a graph node (SynthesizedGap) carrying its full
derivation chain (order-0 postulate -> … -> gap), so the agent OWNS it and the
existing reason_about_gap-style machinery can consume it WITHOUT a hand-seeded
rule. See [[ozma_order_n_concepts]] / [[ozma_analogical_transfer]] /
[[ozma_meta_abilities_are_leverage]] / [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Implication SHAPES — the agent's cross-domain structural knowledge.
#
# NOTE (closure): this _shapes() list is the ORIGINAL hand-curated stencil. It is
# NO LONGER the driver. By default synthesize_gaps() harvests its shapes from the
# agent's OWN concepts via domains/implication_harvester (see _resolve_shapes);
# this stencil is kept only as a fallback (when the agent has no breadth loaded)
# and for the harvested-vs-stencil comparison. The scripts/order_n_postulates_demo
# shows the harvested shapes reproduce these gaps with the stencil OFF.
#
# These are the order-N-over-knowledge analogue of the finite-difference STENCIL:
# each is a structural property a postulate may assert about its object, paired
# with the consequence that property entails. The HARVESTED shapes carry the same
# fields, now sourced from the agent's concepts — the same role analogy.py's
# skeletons play for features. A shape fires by loose STRUCTURAL match
# (keyword-level), exactly like "vaguely similar"; the SELECTOR, not the shape,
# decides whether the consequence is a real gap.
#
# Each shape declares:
#   match_patterns  — loose keyword regexes over a postulate's property text
#                     (when does this structural property hold?);
#   consequence     — the implication it entails;
#   match_keys      — loose keywords the NEXT order matches against this
#                     consequence's text (so derivation recurses); and
#   name_keys       — the DISTINCTIVE, identifying terms for the capability the
#                     consequence names, used by the SELECTOR's coverage / codebase
#                     check. These are specific (e.g. "lpc", "all-pole"), NOT the
#                     loose synonyms, so the selector tests the RIGHT capability.
# ---------------------------------------------------------------------------

def _shapes():
    """The implication-shapes the agent holds across its domains. Returns a list
    of dicts: {name, domain, match_patterns, consequence, match_keys, name_keys}."""
    return [
        # --- from LINEAR ALGEBRA / SIGNALS: a linear system is invertible ------
        {"name": "linear_system_is_invertible", "domain": "linear_algebra",
         "match_patterns": [r"linear\s+filter", r"linear\s+system",
                            r"linear\s+operator", r"\bfilter\b.*\blinear\b",
                            r"\blinear\b.*\bfilter\b"],
         "consequence": (
             "a linear filter is INVERTIBLE — the filtering can be deconvolved "
             "out, so the source and the filter (the resonances) can be "
             "SEPARATED / identified"),
         "match_keys": ["invertible", "deconvolve", "separate", "identify"],
         # cepstral liftering is the canonical homomorphic source/filter
         # separation — a term of art that won't appear casually in a comment.
         "name_keys": ["cepstral liftering", "cepstrum",
                       "homomorphic deconvolution"]},

        # --- from SIGNALS: an invertible LTI filter has a parametric/all-pole model.
        # match_patterns require the DERIVED vocabulary ("invertible", "deconvolved
        # out", "all-resonance") that only order-1's consequence introduces — so
        # this shape fires at order-2 off the invertibility step, not directly off
        # the raw postulate, preserving the 0 -> 1 -> 2 chain.
        {"name": "invertible_filter_has_allpole_model", "domain": "signal_processing",
         "match_patterns": [r"\binvertible\b", r"deconvolv", r"all-resonance"],
         "consequence": (
             "an invertible all-resonance (LTI) filter is captured by an ALL-POLE "
             "(autoregressive / LINEAR-PREDICTIVE, LPC) model — its few poles ARE "
             "the resonances, recovered by linear prediction rather than read off "
             "a blurry spectrum"),
         "match_keys": ["all-pole", "linear predict", "parametric"],
         # canonical LPC terms of art (avoid the loose phrase "linear prediction",
         # which appears in comments describing unrelated averaging).
         "name_keys": ["all-pole", "levinson", "lpc-formant", "autoregressive"]},

        # --- from STATISTICS: a distribution's MODES are its categories --------
        {"name": "distribution_modes_are_clusters", "domain": "statistics",
         "match_patterns": [r"distribut", r"co-?occurr", r"regulariti",
                            r"\bmodes?\b", r"unimodal", r"bimodal"],
         "consequence": (
             "tracking a distribution means finding its MODES — unsupervised "
             "CLUSTERING of the cue values carves the categories at the valleys "
             "between modes, with NO labels"),
         "match_keys": ["cluster", "unsupervised", "mode"],
         # distinctive clustering terms of art. NB: 'k-means' is intentionally
         # NOT used as a coverage key — stt_pipeline.py only MENTIONS k-means in a
         # comment ("same idea as HuBERT iterating k-means…") without implementing
         # cross-speaker clustering, and a source scan cannot tell a comment from
         # an implementation. The distinctive compounds below test the real
         # capability surface; the comment-vs-code limit is noted in the docs.
         "name_keys": ["unsupervised-clustering", "cross-speaker-clustering",
                       "cross-speaker"]},

        # --- from STATISTICS: transitional probability segments a sequence -----
        {"name": "transitional_prob_segments_stream", "domain": "statistics",
         "match_patterns": [r"transitional", r"co-?occurr", r"across\s+syllab",
                            r"word\s+boundar", r"transition.*probab"],
         "consequence": (
             "transitional-probability tracking over a SEQUENCE finds boundaries "
             "where predictability DROPS — word/chunk SEGMENTATION at the "
             "low-probability dips, learned from unlabelled stream statistics"),
         "match_keys": ["boundary", "chunk", "sequence"],
         "name_keys": ["transitional probability", "word-scale chunking",
                       "statistical segmentation", "n-gram boundary"]},

        # --- from PHYSICS/GEOMETRY: a context-dependent quantity is a FUNCTION OF
        #     its context, so the context can be MODELLED and SUBTRACTED ---------
        {"name": "context_dependence_is_a_removable_function", "domain": "physics",
         "match_patterns": [r"context-?dependen", r"depend.*on.*neighbour",
                            r"coarticul", r"non-?invariant", r"vary.*context",
                            r"depend.*neighbour"],
         "consequence": (
             "if a quantity is a smooth FUNCTION of its known context, that "
             "context-effect can be MODELLED and SUBTRACTED — predict the "
             "coarticulatory shift from the neighbours and remove it to recover "
             "the context-free target"),
         "match_keys": ["model", "subtract", "predict"],
         "name_keys": ["coarticulation predict-remove",
                       "context normalization", "carryover removal"]},

        # --- from PHYSICS: a ratio cancels a common scale factor ---------------
        {"name": "ratio_cancels_common_scale", "domain": "physics",
         "match_patterns": [r"vocal-?tract\s+length", r"\bspeaker\b",
                            r"\btalker\b", r"shift.*frequenc",
                            r"scaling.*talker", r"scale.*vocal"],
         "consequence": (
             "a multiplicative/length SCALE factor is cancelled by a RATIO — "
             "normalising formant FREQUENCIES by their ratios (or by a "
             "per-speaker baseline) removes the vocal-tract-length / speaker "
             "scale"),
         "match_keys": ["ratio", "normalise", "scale-invariant"],
         "name_keys": ["speaker normalization", "formant ratio",
                       "vocal-tract-length normalization", "f2/f1"]},

        # --- from MODELLING: an inverse mapping needs a forward model ----------
        {"name": "inverse_needs_forward_model", "domain": "control",
         "match_patterns": [r"invert.*production", r"recover.*from.*cue",
                            r"perception.*inverse", r"inverse\s+map",
                            r"\bimitat", r"reproduce.*target"],
         "consequence": (
             "recovering causes from effects is an INVERSE problem that needs a "
             "FORWARD model (articulation->acoustics) to invert — an internal "
             "synthesiser the loop can run and match against"),
         "match_keys": ["forward model", "synthesise", "analysis-by-synthesis"],
         "name_keys": ["analysis-by-synthesis", "articulatory forward model",
                       "internal synthesiser"]},
    ]


# ---------------------------------------------------------------------------
# Postulate harvesting — the agent's HELD knowledge as order-0 nodes.
# ---------------------------------------------------------------------------

def harvest_postulates(substrate, mt_name=None) -> list:
    """Gather the agent's held postulates: every Concept whose definition+why
    asserts a structural property. Returns [(node_id, name, text)].

    `mt_name` scope:
      · None      — every Mt in the substrate (the full breadth — 139 Mts
                    × 5282 concepts at last count; was the silent bug:
                    callers reaching for synthesize_over_all without
                    passing mt_name saw only ~30 concepts from
                    speech_science).
      · str       — that one Mt's concepts.
      · iterable  — concepts from each of those Mts.

    Backward-compatible: the legacy default value 'speech_science' was the
    silent narrow-scope bug; explicit None now means full breadth. Existing
    callers that pass mt_name='speech_science' still get the same behavior.
    """
    if mt_name is None:
        # Full breadth — every concept under every Mt.
        out = []
        seen = set()
        for mt in substrate.nodes("Microtheory"):
            for c in substrate.neighbours(mt, "has_concept"):
                if c in seen:
                    continue
                seen.add(c)
                a = substrate.node(c)["attrs"]
                name = a.get("name", "")
                text = f"{a.get('definition', '')} {a.get('why', '')}".strip()
                out.append((c, name, text))
        return out
    if isinstance(mt_name, str):
        names = [mt_name]
    else:
        names = list(mt_name)
    out = []
    seen = set()
    for nm in names:
        mt = next((n for n in substrate.nodes("Microtheory")
                   if substrate.node(n)["attrs"].get("name") == nm), None)
        if mt is None:
            continue
        for c in substrate.neighbours(mt, "has_concept"):
            if c in seen:
                continue
            seen.add(c)
            a = substrate.node(c)["attrs"]
            name = a.get("name", "")
            text = f"{a.get('definition', '')} {a.get('why', '')}".strip()
            out.append((c, name, text))
    return out


def _property_text(text: str) -> str:
    return (text or "").lower()


# ---------------------------------------------------------------------------
# The DERIVATIVE — order k -> k+1 by structural transfer (the agent's move).
# ---------------------------------------------------------------------------

def differentiate(property_text: str, articulate=None, shapes=None,
                    *, substrate=None, postulate_term=None,
                    postulate_mt_lineage=None,
                    substantive_structural=False,
                    postulate_mt_hops=None, structural_max_hops=0,
                    structural_broad_mts=None,
                    relevance_active=False,
                    postulate_property_kinds=None,
                    relevance_mode="property") -> list:
    """The order k -> k+1 step: given the PROPERTY a postulate (or a prior
    implication) asserts about its object, transfer every implication-SHAPE whose
    structural pattern matches. Returns a list of derived implications, each a dict
    {consequence, via_shape, source_domain, capability_keys}.

    `shapes` is the implication-shape LIBRARY to transfer from. When None it falls
    back to the hand-curated stencil `_shapes()`; the agent's OWN library is
    supplied by `domains.implication_harvester.harvest_shapes(substrate)` (see
    synthesize_gaps). This is the self-sufficiency seam: with the harvested library
    the shapes come entirely from the agent's own concepts, not from a human list.

    `articulate` (optional) is a peer-LLM hook: articulate(property_text) -> str,
    used ONLY to rephrase the structural property into the agent's vocabulary
    before matching (it does NOT supply the consequence; the agent's shapes do).
    The transfer + the consequence remain the agent's order-N structure."""
    text = _property_text(property_text)
    if articulate is not None:
        try:
            extra = articulate(property_text)
            if extra:
                text = f"{text} {extra.lower()}"
        except Exception:
            pass
    if shapes is None:
        shapes = _shapes()
    # Compute postulate's Shape ONCE when substrate + postulate_term are
    # supplied. Donors with target_shape will be tested against this.
    postulate_shape = None
    if substrate is not None and postulate_term is not None:
        try:
            postulate_shape = substrate.shape_of_term(postulate_term)
        except Exception:
            postulate_shape = None
    out = []
    for sh in shapes:
        pats = sh.get("match_patterns", [])
        # match_mode controls how the shape's patterns combine. The 7
        # regex-extractor kinds (and the hand stencil) use OR ('any') — each
        # pattern is an alternative surface form of one structural property.
        # Rule-derived shapes use 'all': their patterns are the content words
        # of the Rule's antecedent CONJUNCTION, so the shape fires only when
        # the WHOLE structural signature co-occurs — specific, not promiscuous
        # (a single shared word like 'substrate' must not fire it). This is
        # where the harvest's specificity-at-birth is honoured.
        # SHAPE-LIFTED MODE: when a donor has 'target_shape' and the
        # postulate has a Term-tree, use Shape compatibility instead of
        # regex. This is the function_shape pivot's thesis applied to
        # synthesize_gaps — structural similarity, not word overlap.
        # BRICK 2 — STRUCTURAL match by Mt-lineage membership. A concept-graph
        # shape (kind='concept_graph') carries match_kind='mt_lineage' + a
        # source_mt: it fires iff the POSTULATE's concept sits UNDER source_mt in
        # the genlMt lineage (graph structure, the agent's own taxonomy), NOT iff
        # source_mt's name tokens appear in the postulate's PROSE (brick 1's wrong
        # join). The lineage set is precomputed by synthesize_gaps and threaded in
        # as postulate_mt_lineage; with no lineage available the shape cannot fire
        # (we never fall back to regexing the prose for these). source_mt names
        # the owning child Mt, or any ancestor — membership covers both.
        if sh.get("match_kind") == "mt_lineage":
            if not postulate_mt_lineage:
                fired = False
            else:
                src_mt = str(sh.get("source_mt", "")).strip()
                src_mt_id = sh.get("source_mt_id")
                fired = (bool(src_mt) and src_mt in postulate_mt_lineage) or (
                    src_mt_id is not None and src_mt_id in postulate_mt_lineage)
        elif sh.get("match_mode") == "shape" and "target_shape" in sh:
            if postulate_shape is None or substrate is None:
                fired = False
            else:
                try:
                    fired = substrate.shapes_compatible(
                        sh["target_shape"], postulate_shape)
                except Exception:
                    fired = False
        elif sh.get("match_mode") == "all":
            fired = pats and all(re.search(p, text) for p in pats)
        else:
            fired = bool(pats) and any(re.search(p, text) for p in pats)
        # BRICK 3 — STRUCTURAL firing for SUBSTANTIVE shapes. A substantive shape
        # (the 7 regex extractors + the rule-walker: kinds that carry a REAL
        # consequence — invertibility / all-pole / latent-structure / etc.) fires
        # ONLY on text overlap above (5/30 coverage). Brick 3 lets it ALSO fire by
        # STRUCTURE: when the shape's source-domain Mt sits in the postulate's
        # genlMt lineage (the same traversal brick 2 added), transfer its existing
        # consequence/match_keys UNCHANGED — so a postulate inherits the genuine
        # implications harvested from its domain, not a bare is-a edge. The
        # text-overlap firing is KEPT (union). This path is OPT-IN
        # (substantive_structural=True) and skips the concept_graph kind (handled
        # above by mt_lineage) so the is-a filler is not double-fired.
        #
        # PROMISCUITY / RELEVANCE GATE — tightness controls how close the shape's
        # domain Mt must be to the postulate's own Mt (firing every domain shape on
        # every postulate in that domain would flood + transfer irrelevant
        # consequences):
        #   structural_max_hops == 0  : TIGHTEST — source Mt == the postulate's OWN
        #                               Mt (hop 0), same domain only.
        #   structural_max_hops == N  : MEDIUM   — source Mt within N genlMt hops.
        #   structural_max_hops < 0   : LOOSEST  — anywhere in the lineage (brick-2
        #                               reach) via postulate_mt_lineage membership.
        # structural_broad_mts (brick-2's promiscuity gate) drops foundation/near-
        # root domain Mts as sources so a broad hub can't fire on everything.
        if (substantive_structural and not relevance_active and not fired
                and sh.get("kind") not in ("concept_graph", None)
                and sh.get("kind") != "concept_graph"):
            s_mt = str(sh.get("source_mt", "") or "").strip()
            s_id = sh.get("source_mt_id")
            # drop broad/near-root domain Mts as sources (reuse brick-2's gate).
            broad = structural_broad_mts or set()
            is_broad = (s_mt and s_mt in broad) or (s_id is not None
                                                    and s_id in broad)
            if (s_mt or s_id is not None) and not is_broad:
                if structural_max_hops is not None and structural_max_hops < 0:
                    # LOOSEST: anywhere in the lineage set (brick-2 reach).
                    if postulate_mt_lineage:
                        fired = (s_mt and s_mt in postulate_mt_lineage) or (
                            s_id is not None and s_id in postulate_mt_lineage)
                elif postulate_mt_hops:
                    # SAME-Mt (0) / N-hop: the shape's domain Mt must be within
                    # structural_max_hops genlMt steps of the postulate's own Mt.
                    hop = postulate_mt_hops.get(s_mt)
                    if hop is None and s_id is not None:
                        hop = postulate_mt_hops.get(s_id)
                    if hop is not None and hop <= (structural_max_hops or 0):
                        fired = True
        # BRICK 4 — RELEVANCE firing for SUBSTANTIVE shapes. This REPLACES brick
        # 3's "domain Mt in the postulate's lineage" gate (which over-fired: a
        # postulate inherited a domain's shapes merely by sharing an ancestor Mt,
        # even when its OBJECT did not exhibit the structural property the shape's
        # consequence presupposes — 54% cross-domain junk). The relevance gate
        # fires a substantive shape ONLY when the postulate's tagged property_kinds
        # CONTAINS the shape's requires_property (the structural property the
        # consequence presupposes). Two modes:
        #   relevance_mode == "property"            : property match anywhere.
        #   relevance_mode == "property_and_lineage": property match AND the
        #       shape's source-domain Mt within the postulate's genlMt reach
        #       (brick-3's gate, kept as an extra tightness constraint).
        # A shape with requires_property=None (rule-derived FOLKLORE, concept_graph
        # is-a, shape-donor) is NOT structurally fireable by this path — so the
        # "MQTT outperforms HTTP" junk never fires here. The original TEXT path
        # (fired above) is KEPT as a union for all kinds. OPT-IN
        # (relevance_active=True); off by default = no regression.
        if (substantive_structural and relevance_active and not fired
                and sh.get("kind") not in ("concept_graph", None)
                and sh.get("kind") != "concept_graph"):
            req = sh.get("requires_property")
            pkinds = postulate_property_kinds or set()
            if req is not None and req in pkinds:
                if relevance_mode == "property_and_lineage":
                    # ALSO require the shape's domain Mt in the postulate's reach
                    # (and not a broad/near-root hub) — property AND lineage.
                    s_mt = str(sh.get("source_mt", "") or "").strip()
                    s_id = sh.get("source_mt_id")
                    broad = structural_broad_mts or set()
                    is_broad = (s_mt and s_mt in broad) or (
                        s_id is not None and s_id in broad)
                    if not is_broad and postulate_mt_lineage:
                        fired = (s_mt and s_mt in postulate_mt_lineage) or (
                            s_id is not None and s_id in postulate_mt_lineage)
                else:
                    # property-only: the postulate genuinely exhibits the
                    # structural property the consequence presupposes.
                    fired = True
        if fired:
            out.append({
                "consequence": sh["consequence"],
                "via_shape": sh["name"],
                "source_domain": sh["domain"],
                # which of the agent's OWN concepts donated this shape (harvested
                # shapes carry it; the hand stencil leaves it None).
                "source_concept": sh.get("source_concept"),
                # loose keys that let the NEXT order match this consequence:
                "match_keys": list(sh["match_keys"]),
                # distinctive keys the SELECTOR tests for coverage:
                "name_keys": list(sh["name_keys"]),
            })
    return out


# ---------------------------------------------------------------------------
# The SELECTOR — which derived implications are REAL gaps.
#
# An implication is a GAP iff:
#   (a) it is NOT already a held postulate / implemented element — checked against
#       assess_speech_system's covered set AND a codebase scan for the capability
#       keywords; AND
#   (b) it COHERES / COMPRESSES — it actually follows (a shape fired) AND it
#       unifies (its capability keys do not already saturate the covered set).
# Compression is the selector, never an enumerated search.
# ---------------------------------------------------------------------------

# Generic speech words that, on their own, must NOT make a distinctive capability
# look already-covered (e.g. 'formant' is covered, but 'lpc-formant' is not).
_GENERIC = {"formant", "formants", "speaker", "model", "boundary", "context",
            "removal", "coding", "internal", "probability", "mixture",
            "clustering", "cluster", "segmentation", "prediction", "predictive",
            "normalization", "normalisation", "synthesiser",
            "synthesizer", "synthesis", "forward", "model"}


def _covered_keywords(substrate) -> set:
    """The agent's already-realized capability surface, as a keyword set: every
    covered science concept name + every implementation element name (from
    assess_speech_system's own notion of 'implemented')."""
    from .speech_science import assess_speech_system, _impl_names
    words = set()
    try:
        rep = assess_speech_system(substrate)
        for name, hit in rep.get("covered", []):
            words |= {w for w in re.split(r"[\s_]+", f"{name} {hit}".lower())
                      if len(w) > 2}
    except Exception:
        pass
    try:
        impl, _ = _impl_names(substrate)
        for nm in impl:
            words |= {w for w in re.split(r"[\s_]+", nm.lower()) if len(w) > 2}
    except Exception:
        pass
    return words


# The agent's SPEECH-system surface — the modules where a speech capability would
# live if implemented. The codebase scan is scoped HERE, not over the whole repo:
# a gap is "this capability is not in MY speech system", so unrelated DSP (e.g.
# an audio-codec LPC bitstream field) must not mask a missing speech front-end.
#
# CORE_SPEECH_GLOBS is the explicit SEED surface — the speech modules that exist
# regardless of what the agent later builds, plus the Rust auditory primitives
# that have no name-marker a glob could discover. It is NOT the whole surface:
# the openness scan must read the CURRENT speech surface at scan time so that
# capabilities the agent BUILT since this seed was written (the curriculum
# modules: cross_speaker_clustering, allpole_spectral_envelope, continuous, …)
# are correctly seen as CLOSED, not falsely flagged still-open. That live read is
# `_live_speech_globs` below; `_SPEECH_GLOBS` is kept as a name only for the few
# call sites / tests that monkeypatch it (it now just aliases the seed list).
CORE_SPEECH_GLOBS = (
    "domains/phonology.py", "domains/stt_pipeline.py", "domains/sound_graph.py",
    "domains/speech_cortex.py", "domains/speech_development.py",
    "domains/lexical_access.py", "domains/speaker_norm.py",
    "domains/coarticulation_predict_remove.py",
    "domains/recognition_graph.py", "domains/feature_generator.py",
    "domains/order_n_concepts.py", "runners/dsl/src/auditory_cortex.rs",
    "runners/dsl/src/cochlear_nucleus.rs",
    "runners/dsl/src/inferior_colliculus.rs",
)
_SPEECH_GLOBS = CORE_SPEECH_GLOBS  # back-compat alias (tests/scripts may patch it)

# Explicit override for the openness scan surface. When set to a tuple of globs,
# _codebase_has scans EXACTLY that surface; when None (the default) it reads the
# CURRENT live surface (_live_speech_globs). A None sentinel is used — NOT
# object-identity on _SPEECH_GLOBS — because tuple(<tuple>) returns the SAME object
# in CPython, so an `is` check on a "copy" is unreliable. Used to reproduce the
# pre-fix frozen behaviour for the before/after contrast, or by a test that wants a
# fixed surface.
_SPEECH_GLOBS_OVERRIDE = None

# Name-markers that identify a domains/*.py module as part of the agent's speech /
# perception / recognition surface. A module whose stem contains any of these is a
# place a speech capability would live — so the live scan discovers curriculum-
# built modules (e.g. cross_speaker_clustering, allpole_spectral_envelope,
# speaker_invariant_centroids, distributional_categories, continuous,
# forward_segmentation, …) without naming any one of them. This is FILE DISCOVERY
# over the current surface, not a capability list: the is_gap / _codebase_has
# distinctive-token scan still decides which capability (if any) lives in each.
_SPEECH_MODULE_MARKERS = (
    "invariant", "cluster", "allpole", "lpc", "cepstr", "continuous",
    "frication", "sonority", "segment", "speaker", "distributional",
    "centroid", "formant", "forward", "representation", "voice",
    "grounding", "fusion", "ear", "cochlea", "phon", "acoustic",
    "auditory", "perception", "spectral", "vowel", "lexic", "coarticul",
)


def _live_speech_globs(search_root) -> tuple:
    """The agent's CURRENT speech-system surface, read from disk AT SCAN TIME.

    This is the live-glob residual: the openness selector must scan what the
    agent's speech system ACTUALLY contains now, not a frozen snapshot taken
    before the curriculum built its perception modules. Returns the explicit
    seed surface (CORE_SPEECH_GLOBS) UNION every `domains/*.py` whose name marks a
    speech / perception / recognition capability (`_SPEECH_MODULE_MARKERS`). Pure
    mechanical file discovery — it asserts nothing about which capability lives in
    which file (the distinctive-token scan in `_codebase_has` decides that). With
    no disk access it degrades to the seed surface, so behaviour is never worse
    than the old frozen list."""
    from pathlib import Path
    root = Path(search_root)
    globs = list(CORE_SPEECH_GLOBS)
    seen = set(globs)
    try:
        for f in sorted((root / "domains").glob("*.py")):
            rel = f"domains/{f.name}"
            if rel in seen:
                continue
            stem = f.stem.lower()
            if stem.startswith("test"):
                continue
            if any(m in stem for m in _SPEECH_MODULE_MARKERS):
                globs.append(rel)
                seen.add(rel)
    except Exception:
        pass
    return tuple(globs)


def _codebase_has(name_keys: list, search_root) -> str | None:
    """Scan the agent's SPEECH-system surface for a DISTINCTIVE capability name.
    Returns the first speech-module file that implements it, or None. A capability
    counts as present in a file iff ALL its distinctive tokens (generic words
    stop-listed) appear in that file's source OR its filename — so a multi-word
    name like 'coarticulation predict-remove' matches the module that does it even
    when the exact phrase isn't written. Speech scoping + distinctive tokens keep
    this precise (unrelated DSP elsewhere in the repo can't mask a real gap)."""
    from pathlib import Path
    root = Path(search_root)
    # The openness scan reads the agent's CURRENT speech surface (the live-glob
    # residual): the seed list UNION the curriculum-built speech modules on disk.
    # Resolution order:
    #   1. an EXPLICIT _SPEECH_GLOBS_OVERRIDE tuple (a caller forcing a fixed
    #      surface — e.g. the frozen-vs-live contrast, or a test);
    #   2. a _SPEECH_GLOBS that a caller has REPLACED with a non-core surface
    #      (legacy back-compat for code that monkeypatched _SPEECH_GLOBS directly);
    #   3. otherwise DISCOVER LIVE (the default) — what the agent's speech system
    #      actually contains now, not the frozen seed snapshot.
    if _SPEECH_GLOBS_OVERRIDE is not None:
        scan_globs = _SPEECH_GLOBS_OVERRIDE
    elif _SPEECH_GLOBS is not CORE_SPEECH_GLOBS:
        scan_globs = _SPEECH_GLOBS
    else:
        scan_globs = _live_speech_globs(root)
    files = [root / g for g in scan_globs if (root / g).exists()]
    if not files:
        return None
    # Split on whitespace/underscore/slash only — NOT hyphen, so technical
    # compounds ('all-pole', 'lpc-formant') stay intact as one distinctive token.
    # A name matches a file iff ALL its residual tokens (generic words dropped)
    # appear in the file AND at least one of them is RARE (>=5 chars or a
    # hyphenated compound) — so a leftover generic token ('cross', 'all') alone
    # cannot mark a capability present.
    name_tokensets = []
    for nm in name_keys:
        toks = [t for t in re.split(r"[\s_/]+", nm.lower())
                if len(t) > 2 and t not in _GENERIC]
        if toks and any(len(t) >= 5 or "-" in t for t in toks):
            name_tokensets.append((nm, toks))
    if not name_tokensets:
        return None
    for f in files:
        try:
            text = f.read_text(errors="ignore").lower()
        except Exception:
            continue
        hay = f"{text} {f.stem.replace('_', ' ').lower()}"
        for nm, toks in name_tokensets:
            if all(re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", hay)
                   for t in toks):
                return str(f)
    return None


def is_gap(substrate, implication: dict, covered_kw: set, search_root,
           prune: bool = True) -> dict:
    """The selector. An implication is a GAP iff it is NOT a held / implemented
    capability AND it coheres. Returns {is_gap, reason, covered_by}. Coverage is
    tested with the DISTINCTIVE name_keys (the capability's identifying terms),
    not the loose match keys, so the right capability is checked.

    `prune` (default True) is the order in which the two distinct questions are
    asked. The synthesis pipeline answers TWO things about every transferred
    implication that are easy to conflate (the conflation is what produced the
    stale "MISS LPC" reading):
      • DERIVATION — does a shape TRANSFER onto this postulate and produce this
        consequence at all? (the harvester's job; "self-sufficiency".)
      • OPENNESS  — given that it derives, is the capability STILL un-realized?
        (the selector's job; checked against the science/impl surface + a scan of
        the agent's speech codebase.)
    With prune=False the selector reports DERIVATION only — it returns is_gap for
    every coherent implication WITHOUT testing whether the agent has since
    IMPLEMENTED it. This lets self-sufficiency ("the harvested shapes DERIVE the
    known capability") be measured independent of whether the agent already acted
    on it (e.g. LPC, which the iter-2 loop implemented in sound_graph.py, so it is
    correctly no longer an OPEN gap but is still correctly DERIVABLE). This split
    is GENERAL — it is not specific to LPC or to any shape."""
    names = [k.lower() for k in implication.get("name_keys", [])]
    if not prune:
        # DERIVATION-only: the shape transferred and named a capability; report it
        # without asking whether the agent has since realized it.
        return {"is_gap": True,
                "reason": "derived by transfer (prune off: openness not tested)",
                "covered_by": None}
    # (a1) already covered by the agent's science/impl surface? Require the
    # DISTINCTIVE tokens of a capability name to ALL be covered — not just a
    # generic shared word (e.g. 'formant' alone must not make 'lpc-formant' look
    # covered). Generic speech words are stop-listed so the rare term must match.
    for nm in names:
        toks = [t for t in re.split(r"[\s_/-]+", nm)
                if len(t) > 2 and t not in _GENERIC]
        if toks and all(any(t == cw or t in cw for cw in covered_kw)
                        for t in toks):
            return {"is_gap": False, "reason": "already covered (science/impl)",
                    "covered_by": nm}
    # (a2) already in the agent's speech codebase?
    code_hit = _codebase_has(names, search_root)
    if code_hit:
        return {"is_gap": False, "reason": "already in speech codebase",
                "covered_by": code_hit}
    # (b) coherence/compression: a shape fired (it follows) AND it names a
    # genuinely NEW capability axis (it unifies / compresses, not a re-label).
    return {"is_gap": True,
            "reason": "follows by transfer + un-realized + new capability axis",
            "covered_by": None}


# ---------------------------------------------------------------------------
# The OPERATOR — recursive order-N synthesis over a postulate (re-runnable).
# ---------------------------------------------------------------------------

def _mt_lineage_of_concept(substrate, concept_nid) -> set:
    """The genlMt LINEAGE of a postulate's Concept, as graph structure: the
    Concept's owning Mt(s) (incoming has_concept) plus every ancestor reached by
    walking genlMt (child --genlMt--> parent) upward. Returned as a set holding
    BOTH the Mt node-ids AND their names, so a concept_graph shape's source_mt
    (a name) or source_mt_id (an id) can be tested for membership. This is the
    structural join brick 2 uses instead of regexing the postulate's prose."""
    if concept_nid is None:
        return set()
    g = substrate.graph_to_dict()
    name_of = {nd["id"]: str(nd["attrs"].get("name", "") or "")
               for nd in g["nodes"]}
    # genlMt: child -> [parents]; has_concept: mt -> [concepts] (we want inverse)
    parents: dict = {}
    owning_mts: set = set()
    for e in g["edges"]:
        if e["type"] == "genlMt":
            parents.setdefault(e["src"], []).append(e["tgt"])
        elif e["type"] == "has_concept" and e["tgt"] == concept_nid:
            owning_mts.add(e["src"])
    lineage_ids: set = set()
    stack = list(owning_mts)
    while stack:
        m = stack.pop()
        if m in lineage_ids:
            continue
        lineage_ids.add(m)
        stack.extend(parents.get(m, []))
    out: set = set(lineage_ids)
    for m in lineage_ids:
        nm = name_of.get(m, "")
        if nm:
            out.add(nm)
    return out


def _mt_lineage_hops_of_concept(substrate, concept_nid) -> dict:
    """Like _mt_lineage_of_concept but returns HOP DISTANCE: {mt_id: hops,
    mt_name: hops}, where the postulate's OWN owning Mt(s) are hop 0, their
    genlMt parents hop 1, grandparents hop 2, … (BFS up the taxonomy). Brick 3's
    tightness gate uses this: structural_max_hops==0 means the substantive shape's
    domain Mt must BE the postulate's own Mt (same domain); ==N allows N genlMt
    steps; <0 falls back to flat lineage membership. Both id and name keys are
    populated so a shape's source_mt (name) or source_mt_id (id) resolves."""
    if concept_nid is None:
        return {}
    g = substrate.graph_to_dict()
    name_of = {nd["id"]: str(nd["attrs"].get("name", "") or "")
               for nd in g["nodes"]}
    parents: dict = {}
    owning_mts: set = set()
    for e in g["edges"]:
        if e["type"] == "genlMt":
            parents.setdefault(e["src"], []).append(e["tgt"])
        elif e["type"] == "has_concept" and e["tgt"] == concept_nid:
            owning_mts.add(e["src"])
    hops: dict = {}
    # BFS from the owning Mts (hop 0), keeping the MINIMUM hop to each ancestor.
    frontier = [(m, 0) for m in owning_mts]
    visited: set = set()
    while frontier:
        m, d = frontier.pop(0)
        if m in visited and hops.get(m, 10 ** 9) <= d:
            continue
        visited.add(m)
        if d < hops.get(m, 10 ** 9):
            hops[m] = d
        for p in parents.get(m, []):
            frontier.append((p, d + 1))
    out: dict = {}
    for m, d in hops.items():
        out[m] = d
        nm = name_of.get(m, "")
        if nm and (nm not in out or out[nm] > d):
            out[nm] = d
    return out


def _resolve_shapes(substrate, shapes):
    """Pick the implication-shape library. Modes:
      • shapes="harvested" / None : the agent's OWN shapes, harvested from its
        concepts (domains.implication_harvester) — the self-sufficient path. Falls
        back to the hand stencil ONLY if the harvest comes up empty.
      • shapes="stencil"          : the hand-curated stencil (_shapes()) — kept for
        comparison / as a fallback.
      • shapes="both"             : harvested ∪ stencil (de-duplicated by name).
      • shapes=<list>             : an explicit library.
    Returns (shape_list, mode_label)."""
    if isinstance(shapes, list):
        return shapes, "explicit"
    if shapes == "stencil":
        return _shapes(), "stencil"
    # Use the COMBINED harvester (regex-extractor shapes + rule-walker
    # shapes from commit 7dced20). The original harvest_shapes returned
    # only the 7 regex shapes; harvest_shapes_combined adds ~500
    # rule-derived shapes from the substrate's Rule nodes. Before this
    # fix, synthesize_gaps was downstream-blocked by the harvester's
    # narrow output — the substrate's 1086 rules expressing explicit
    # if->then implications were not reaching the differentiation
    # pipeline.
    try:
        from .implication_harvester import harvest_shapes_combined
        harvested = harvest_shapes_combined(substrate)
    except Exception:
        try:
            from .implication_harvester import harvest_shapes
            harvested = harvest_shapes(substrate)
        except Exception:
            harvested = []
    # SHAPE-LIFTED DONORS — function_shape pivot's thesis applied to
    # synthesize_gaps. The Shape-lifted harvester returns donors keyed
    # by Shape (recursion/order_n/abstraction) instead of by regex
    # keywords. Merged with the regex donors so callers see both.
    try:
        from .harvester_shape import harvest_shape_donors_compatible
        shape_donors = harvest_shape_donors_compatible(substrate)
        harvested = harvested + shape_donors
    except Exception:
        pass
    if shapes == "both":
        seen = {s["name"] for s in harvested}
        merged = harvested + [s for s in _shapes() if s["name"] not in seen]
        return merged, "harvested+stencil"
    # default / "harvested": the agent's own shapes, with the stencil only as a
    # safety net if the agent has no breadth loaded at all.
    if harvested:
        return harvested, "harvested"
    return _shapes(), "stencil(fallback:empty-harvest)"


def synthesize_gaps(substrate, postulate_name: str, max_order: int = 3,
                    articulate=None, search_root=None,
                    record: bool = True, shapes=None, prune: bool = True,
                    substantive_structural: bool = False,
                    structural_max_hops: int = 0,
                    structural_broad_mts=None,
                    relevance_active: bool = False,
                    relevance_mode: str = "property") -> list:
    """Run the order-N-postulate operator over ONE held postulate, by name.

    Recursively differentiates (order 0 -> 1 -> … -> max_order), following each
    order-(k) implication's structural property into order-(k+1), and tests every
    derived implication against the selector. Returns a list of synthesized gaps,
    each a dict:
        {gap, capability_keys, order, chain: [order-0 text, …, gap text],
         via_shapes, source_domains, source_concepts, node (if recorded)}
    The same call works over ANY postulate name — it is the general operator, not
    a hand-fit to one answer.

    `shapes` selects the implication-shape library (see _resolve_shapes): the
    DEFAULT is the agent's OWN harvested shapes (self-sufficient — no human
    stencil); pass "stencil" for the hand-curated comparison or "both" for the
    union.

    `prune` (default True): when True a derived implication is only returned if the
    selector judges it an OPEN gap (not already realized — see is_gap). When False
    the openness test is skipped and every coherent DERIVED implication is
    returned, so harvester self-sufficiency (does the transfer produce the
    capability at all?) can be measured independent of whether the agent has since
    IMPLEMENTED it."""
    if search_root is None:
        from pathlib import Path
        search_root = Path(__file__).resolve().parent.parent
    posts = {nm: (cid, txt)
             for cid, nm, txt in harvest_postulates(substrate)}
    if postulate_name not in posts:
        return []
    cid0, text0 = posts[postulate_name]
    covered_kw = _covered_keywords(substrate)
    shape_lib, _mode = _resolve_shapes(substrate, shapes)
    # BRICK 2: precompute the postulate concept's genlMt lineage ONCE — the
    # structural join the mt_lineage concept-graph shapes fire on (graph
    # membership, not prose regex). Threaded into differentiate below.
    try:
        postulate_mt_lineage = _mt_lineage_of_concept(substrate, cid0)
    except Exception:
        postulate_mt_lineage = set()
    # BRICK 3: when substantive-structural firing is opted in, also precompute the
    # postulate's Mt HOP-DISTANCE map (own Mt = 0, parents = 1, …) so the tightness
    # gate (same-Mt / N-hop) can decide which substantive domain shapes may fire.
    postulate_mt_hops = None
    if substantive_structural:
        try:
            postulate_mt_hops = _mt_lineage_hops_of_concept(substrate, cid0)
        except Exception:
            postulate_mt_hops = {}
    # BRICK 4: the postulate's tagged structural property-KINDs — the set the
    # relevance gate tests a shape's requires_property against. Read from the
    # Concept's property_kinds attr (populated by tag_concept_properties). If the
    # concept was never tagged the set is empty and the relevance path fires
    # nothing (correct: an untagged object cannot be asserted to exhibit a
    # property). The text path still fires regardless.
    postulate_property_kinds = set()
    if relevance_active:
        try:
            from .implication_harvester import concept_property_kinds
            postulate_property_kinds = concept_property_kinds(substrate, cid0)
        except Exception:
            postulate_property_kinds = set()

    gaps = []
    seen = set()                       # dedup by capability-key signature

    # frontier of (order, property_text, chain, used_shapes, domains, concepts)
    frontier = [(0, text0, [f"order-0: {postulate_name} — {text0}"], [], [], [])]
    while frontier:
        order, prop, chain, used, domains, concepts = frontier.pop(0)
        if order >= max_order:
            continue
        # Look up the postulate's Term-tree if one is registered. When
        # present, differentiate uses Shape compatibility for any donor
        # with target_shape. Falls back to regex for postulates without
        # Term-trees.
        try:
            from .harvester_shape import lookup_postulate_term
            postulate_term = lookup_postulate_term(postulate_name)
        except Exception:
            postulate_term = None
        for impl in differentiate(prop, articulate=articulate,
                                  shapes=shape_lib,
                                  substrate=substrate,
                                  postulate_term=postulate_term,
                                  postulate_mt_lineage=postulate_mt_lineage,
                                  substantive_structural=substantive_structural,
                                  postulate_mt_hops=postulate_mt_hops,
                                  structural_max_hops=structural_max_hops,
                                  structural_broad_mts=structural_broad_mts,
                                  relevance_active=relevance_active,
                                  postulate_property_kinds=postulate_property_kinds,
                                  relevance_mode=relevance_mode):
            # dedup by the CAPABILITY the implication names (its distinctive
            # name_keys), not by the shape that fired — so the same gap derived via
            # the harvested shape AND the stencil shape (in "both" mode) is reported
            # once, and the harvested/stencil recall comparison is apples-to-apples.
            sig = frozenset(k.lower() for k in impl.get("name_keys", []))
            # provenance: which of the agent's own concepts donated this shape
            # (harvested shapes carry source_concept; the stencil leaves it None).
            via = impl["via_shape"]
            src_c = impl.get("source_concept")
            via_label = f"{impl['source_domain']}:{via}"
            if src_c:
                via_label += f" (from concept '{src_c}')"
            new_chain = chain + [
                f"order-{order + 1} (via {via_label}): {impl['consequence']}"]
            new_used = used + [via]
            new_domains = domains + [impl["source_domain"]]
            new_concepts = concepts + ([src_c] if src_c else [])
            verdict = is_gap(substrate, impl, covered_kw, search_root,
                             prune=prune)
            if verdict["is_gap"] and sig not in seen:
                seen.add(sig)
                gap = {
                    "gap": impl["consequence"],
                    "capability_keys": impl["name_keys"],
                    "order": order + 1,
                    "chain": new_chain,
                    "via_shapes": new_used,
                    "source_domains": new_domains,
                    "source_concepts": new_concepts,
                    "from_postulate": postulate_name,
                }
                if record:
                    gap["node"] = _record_gap(substrate, cid0, gap)
                gaps.append(gap)
            # recurse: the consequence's property feeds the next order. (Skip a
            # shape already used on this branch so the recursion terminates.)
            if via not in used:
                frontier.append((order + 1, impl["consequence"], new_chain,
                                 new_used, new_domains, new_concepts))
    return gaps


def _record_gap(substrate, postulate_nid, gap: dict):
    """Mint the synthesized gap as a graph node the agent OWNS, with its full
    derivation chain, so reason_about_gap-style machinery can consume it WITHOUT a
    hand-seeded rule. Returns the node id."""
    try:
        substrate.add_production({
            "src": {"type": "SynthesizedGap", "var": "a"},
            "edge_type": "derived_from",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "order_n_postulates:derived_from"})
    except Exception:
        pass
    g = substrate.add_node("SynthesizedGap", {
        "gap": gap["gap"],
        "from_postulate": gap["from_postulate"],
        "order": gap["order"],
        "capability_keys": list(gap["capability_keys"]),
        "derivation_chain": list(gap["chain"]),
        "via_shapes": list(gap["via_shapes"]),
        "source_domains": list(gap["source_domains"]),
        "source_concepts": list(gap.get("source_concepts", [])),
        "origin": "order_n_postulate_synthesis",
        "composed_by": "agent",
    })
    try:
        substrate.add_edge(g, "derived_from", postulate_nid, {})
    except Exception:
        pass
    return g


def synthesize_over_all(substrate, mt_name=None,
                        max_order: int = 3, articulate=None,
                        search_root=None, record: bool = True,
                        shapes=None, prune: bool = True) -> dict:
    """Run the operator over EVERY held postulate in a microtheory — the agent
    synthesizing its full gap-map from its own knowledge. Returns
    {postulate_name: [gaps]} for the postulates that yielded any. `shapes` selects
    the implication-shape library (default: the agent's own harvested shapes).
    `prune` (default True) gates on openness; prune=False reports every DERIVED
    implication (self-sufficiency, regardless of later implementation).

    `mt_name`: see harvest_postulates. None = full breadth (every Mt);
    str = single Mt; iterable = subset. Default changed from 'speech_science'
    to None — the prior default was a silent narrow-scope bug surfaced by
    the self-audit (commit f372805): synthesize_over_all called without
    explicit mt_name only differentiated speech postulates, even though
    the agent now holds theory across 139 Mts."""
    out = {}
    for _, name, _ in harvest_postulates(substrate, mt_name):
        gaps = synthesize_gaps(substrate, name, max_order=max_order,
                               articulate=articulate, search_root=search_root,
                               record=record, shapes=shapes, prune=prune)
        if gaps:
            out[name] = gaps
    return out


__all__ = ["harvest_postulates", "differentiate", "is_gap", "synthesize_gaps",
           "synthesize_over_all"]

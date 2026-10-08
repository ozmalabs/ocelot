"""arm — the decode-through-ToM text arm driver (INDUCED_BELIEF_PREREG.md).

STRICT REUSE. This module is a WORLD ADAPTER (CLAUDE.md): it marshals graph in,
ticks, and reads out. Every DECISION is a seed rule (ib_decode_stance) or the
CAN marginal <sigma>. The pipeline, exactly as preregistered:

  utterance (corpus Message, tick=asof-bounded)
    -> frame.ground_frame: the frame DECODE, surface -> (symbol, motion)
    -> mint one FrameReading{symbol, motion, market} per hit             [graph in]
    -> ib_decode_stance RULE: FrameReading (symbol,motion) Eq-join CBSpeechAct
       -> StanceReading{attr:"<stance>_stance_for:<market>", sign, direction} [DECISION = rule]
    -> native.concept_apply_evidence on the target-scoped CAN Concept        [REUSE]
       (applied DIRECTLY on the boot-cached Concept map — the SAME belief-update
        primitive reasoning_can_bridge.apply_derived_fact_as_can_evidence calls
        at reasoning_can_bridge.py:227; the bridge itself is exercised ONCE at
        boot to mint the SmEntity-denotes->Mt edge, then the per-utterance decode
        applies evidence to the resolved Concept directly, not through the bridge)
    -> force_all_dirty() + run_rules(): relax the CAN network            [GOTCHA honored]
    -> the winning stance = the held Argmax Term over the CONFIRMED stance
       Concepts' CAN marginals <sigma> (Concept.state) — the SELECTION is
       graph-native (native.evaluate), not a Python argmax                 [read out]
    -> grounding_reach transitive read (ReachableFrom 'grounded_in') IS the
       confidence; a chain reaching no anchor mints GroundingGap, shift~0 [REUSE]
    -> direction(<winning stance>) x grounding_weight -> the forecast-band shift.
       The direction is READ off the winning StanceReading's `direction` graph
       datum (the codebook sign->direction mapping, carried by the rule), not
       decided by a Python if/elif.

The market is modeled as a bigville RESIDENT (strict reuse of
worlds.bigville_can_beliefs.build_resident_can_mt), so the target-scoped stance
Concepts live in a CAN belief Microtheory the SmEntity the utterance grounds
DENOTES (via the UNCHANGED entity_concept_correspondence rules the bridge runs
ONCE at boot).
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import reasoning_can_bridge as rcb          # noqa: E402  (REUSE)
from domains import grounding_reach as gr                # noqa: E402  (REUSE)
from domains import shared_arousal as sa                 # noqa: E402  (REUSE)
from domains import bigville_theory_of_mind as tom       # noqa: E402  (REUSE)
from worlds import bigville_can_beliefs as bcb           # noqa: E402  (REUSE)

from . import frame                                       # noqa: E402

_CODEBOOK_SEED = os.path.join(_HERE, "induced_belief_codebook.json")
_SEED_SENTINEL = "induced_belief_codebook"

# the stance aspects our codebook can emit (for pre-minting the target-scoped
# Concepts on the market Mt — mint_target_concept is idempotent).
_STANCES = ("hawkish", "dovish", "neutral")


# --------------------------------------------------------------------------- #
#  the held Argmax readout — the winning-stance SELECTION as GRAPH DATA, not a
#  Python argmax loop. Mirrors coref_entities.antecedent_argmax_term /
#  many_settings_recognizer.predict_many_settings_term: an `Argmax` Term over the
#  target-scoped stance Concepts (a NodesWhere source scoped by the `ib_stance_
#  market` DATA tag build_market stamps), ranked by the CAN marginal `state`,
#  restricted to the CONFIRMED stances (state > 0) exactly as the prior Python
#  `if st <= 0: continue` did. Evaluated natively (native.evaluate); Python never
#  picks the winner — it only reads the winning Concept's name back.
# --------------------------------------------------------------------------- #
def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _Filter(src, var, pred): return {"type": "Filter", "source": src,
                                     "var_name": var, "predicate": pred}
def _Argmax(src, var, val, default): return {"type": "Argmax", "source": src,
                                             "var_name": var, "value": val,
                                             "default": default}


def _winning_stance_term(market: str) -> dict:
    """Argmax over the market's CONFIRMED stance Concepts of the CAN marginal
    `state` — the winning stance as the graph's own selection.

        Argmax( Filter( NodesWhere(Concept, ib_stance_market==market), c,
                        Gt(c.state, 0) ),          # only CONFIRMED stances
                c, c.state, default=None )          # ranked by the marginal
    """
    c = _V("c")
    confirmed = _Filter(
        _NodesWhere("Concept", "ib_stance_market", _Lit(market)),
        "c", _Gt(_Attr(c, "state"), _Lit(0.0)))
    return _Argmax(confirmed, "c", _Attr(c, "state"), None)


# --------------------------------------------------------------------------- #
#  boot helpers — mechanical, idempotent
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def ensure_codebook_seed(agent) -> bool:
    """Idempotently install induced_belief_codebook.json's rule (the
    ib_decode_stance DECISION). Guard: the sentinel Concept — the SAME
    ensure_seeds idiom reasoning_can_bridge / inference_generation use."""
    sub, native = _resolve(agent)
    if _has_concept(sub, _SEED_SENTINEL):
        return False
    from substrate.seed_loader import engine_rules_only
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    native.load_seed_manifest(engine_rules_only(manifest))
    return True


def teach_codebook(agent) -> dict:
    """Teach the frame-symbol Concepts + the CBSpeechAct codebook nodes as
    DATA (CLAUDE.md teach facility shape). Idempotent. The frame symbols are
    Concept nodes (so read_clause's mention_resolves_to_concept rule can ground
    to them); the codebook entries are CBSpeechAct nodes the ib_decode_stance
    rule Eq-joins against. Returns counts."""
    sub, native = _resolve(agent)
    counts = {"symbols": 0, "codebook": 0}

    # (A) frame-symbol Concepts — taught vocabulary, find-or-create by name.
    for name in frame.FRAME_SYMBOLS:
        if not _has_concept(sub, name):
            sub.add_node("Concept", {"name": name, "domain": "forecast_frame"})
            counts["symbols"] += 1

    # (C) codebook — one CBSpeechAct per entry, keyed on (symbol, motion),
    #     idempotent by that key. The self-edge is_cb_speech_act is what the
    #     ib_decode_stance rule matches on (the same is_entity self-edge idiom
    #     situation_model_reader uses to make a node rule-matchable).
    existing = {}
    for n in sub.nodes("CBSpeechAct"):
        at = sub.node(n)["attrs"]
        existing[(at.get("symbol"), at.get("motion"))] = n
    for entry in frame.codebook_entries():
        key = (entry["symbol"], entry["motion"])
        if key in existing:
            continue
        cb = sub.add_node("CBSpeechAct", dict(entry))
        try:
            native.add_edge_unchecked(cb, "is_cb_speech_act", cb)
        except TypeError:
            native.add_edge_unchecked(cb, "is_cb_speech_act", cb, {})
        counts["codebook"] += 1
    return counts


def build_market(agent, *, market: str = None):
    """Build the market as a bigville RESIDENT (strict reuse of
    build_resident_can_mt) whose CAN belief Mt will hold the target-scoped
    stance Concepts. Pre-mints the <stance>_stance_for:<market> Concepts via
    mint_resident_tom_belief (mint_target_concept) so the bridge's name lookup
    resolves. Returns {resident, mt, concepts:{attr->node}, sm_entity}.
    Idempotent: reuses an existing market resident."""
    sub, native = _resolve(agent)
    market = market or frame.MARKET

    # find-or-build the market Resident + its belief Mt (build_resident_can_mt
    # expects a resident dict shaped like bigville_cast100.json's entries).
    res_node = None
    for r in sub.nodes("Resident"):
        if sub.node(r)["attrs"].get("name") == market:
            res_node = r
            break
    if res_node is None:
        resident = {
            "name": market, "index": 9000,
            "params": {
                "resolution_bins": 8.0, "arousal": 0.0,
                "prior_world_safe": 0.5, "prior_self_worth": 0.5,
                "prior_others_trust": 0.5, "charm_weight": 0.0,
                "hostile_weight": 0.0, "claim_weight": 1.0, "cred_on": 1.0,
                "w_supergraph": 0.5, "w_spite": 0.0,
            },
        }
        bcb.install_productions(native)
        built = bcb.build_resident_can_mt(native, resident)
        res_node = built["resident_node"]
        mt = built["mt_node"]
    else:
        mt = native.neighbours(res_node, "has_belief_mt")[0]

    # 3-state discrete relaxation mode (same config the CAN native engine and
    # grow_can_network_from_text expect).
    sub.set_attr(mt, "discrete_mode", "3state")
    if sub.node(mt)["attrs"].get("can_tick") is None:
        sub.set_attr(mt, "can_tick", 0.0)

    # pre-mint the target-scoped stance Concepts (idempotent). Tag each with a
    # small DATA marker (`ib_stance_market`) so the graph-native Argmax readout
    # can enumerate EXACTLY these three stance Concepts as its candidate set
    # (a NodesWhere source), not every Concept on the Mt. Mechanical adapter
    # tagging at mint time — the same one-time-init discipline state/
    # external_field use; carries no decision.
    concepts = {}
    for stance in _STANCES:
        c = tom.mint_resident_tom_belief(native, mt, "%s_stance" % stance, market)
        sub.set_attr(c, "ib_stance_market", market)
        concepts[frame._attr(stance)] = c

    # the SmEntity that DENOTES this Mt — minted here by name so the bridge's
    # correspondence rules (exact-name) mint the denotes edge. read_clause would
    # also mint it if the market name appears in the utterance; pre-minting by
    # the market name guarantees the denotes edge regardless of surface wording.
    from domains import situation_model_reader as smr
    ent = smr._entity(agent, market)

    # Establish the SmEntity -denotes-> Mt edge ONCE, now, by driving the
    # UNCHANGED reused bridge a single time (apply_derived_fact_as_can_evidence
    # runs the entity_concept_correspondence rules and mints the denotes edge).
    # Doing this once at boot means the per-utterance decode does NOT re-run the
    # full correspondence fixpoint 52x (the measured per-snippet cost). We then
    # cache the resolved (attr -> concept) map the decode applies evidence to
    # directly via native.concept_apply_evidence — the SAME belief-update
    # primitive the bridge calls (reasoning_can_bridge.py:227) and that
    # worlds.bigville_can_beliefs.apply_scenario_evidence / hate_attribution
    # already call directly; strict reuse, just resolved once not per-read.
    warm_attr = frame._attr("hawkish")
    rcb.apply_derived_fact_as_can_evidence(agent, market, warm_attr,
                                           positive=True, alpha=1.0)
    # zero the warm-up evidence so boot leaves beliefs at rest.
    for stance in _STANCES:
        c = concepts[frame._attr(stance)]
        sub.set_attr(c, "external_field", 0.0)
        sub.set_attr(c, "state", 0.0)
    native.force_all_dirty()
    native.run_rules(64)

    return {"resident": res_node, "mt": mt, "concepts": concepts,
            "sm_entity": ent, "market": market}


def boot(agent, *, market: str = None) -> dict:
    """One-shot idempotent boot of the whole arm on `agent`. Returns the market
    handle from build_market plus seed/teach counts."""
    # the CAN native discrete-relaxation engine (can_native_update_3state etc.)
    # must be loaded for concept_apply_evidence's external_field to propagate
    # into the Concept's state (the marginal <sigma>). REUSE of the SAME loader
    # solver_dispatch.grow_can_network_from_text uses.
    from domains import solver_dispatch as sd
    sd.ensure_can_native_engine_loaded(agent)
    ensure_codebook_seed(agent)
    counts = teach_codebook(agent)
    mk = build_market(agent, market=market)
    mk["teach_counts"] = counts
    return mk


# --------------------------------------------------------------------------- #
#  the read — one utterance -> (direction, marginal, grounding, shift)
# --------------------------------------------------------------------------- #
def _read_clause_predications(agent, text):
    """Ground the utterance via the UNCHANGED reading_collapse.read_clause —
    the corpus-route reader. We do not consume its predications directly for the
    stance (the frame decode does that), but calling it grounds the utterance's
    mentions into the situation model exactly as the corpus route does, so the
    utterance is a first-class read clause, not a bare string."""
    from domains import reading_collapse as rc
    try:
        return rc.read_clause(agent, text, write=False, learn=False)
    except Exception:
        return {"predications": [], "speech_act": "statement"}


def _mint_message(agent, text, *, tick=0, market=None):
    """Ingest the utterance as a corpus Message from outside the agent — the
    SensorAnchor-eligible provenance node (grounding_reach maps a Message to a
    SensorAnchor). source='corpus' is stamped for provenance; we mint the
    grounded_in edge explicitly for a grounded frame decode (see below)."""
    sub, native = _resolve(agent)
    mid = sub.add_node("Message", {"text": str(text), "source": "corpus",
                                   "tick": float(tick),
                                   "market": market or frame.MARKET})
    return mid


def decode_utterance(agent, text, mk, *, tick=0, alpha=1.0,
                     confident_override=None):
    """Decode ONE utterance to a graded, grounding-weighted forecast signal.

    Returns a dict:
      {direction: up|down|none, marginal: <sigma> of the winning stance,
       grounding_weight: [0,1], reached: bool, hops: int|None,
       grounding_gap: bool, base_shift, shift, stances:[...], frame_hits:[...]}

    `confident_override` (for H3): a (symbol, motion, sign) the caller forces a
    StanceReading for WITHOUT a real frame ground — an ungrounded-but-confident
    read. Its provenance chain reaches no anchor, so grounding_reach flags a
    GroundingGap and the shift attenuates to ~0.
    """
    sub, native = _resolve(agent)
    market = mk["market"]

    # 1. read the clause (corpus route) — grounds the utterance's mentions.
    whole = _read_clause_predications(agent, text)

    # 2. FRAME DECODE: surface -> (symbol, motion) hits.
    hits = frame.ground_frame(text)

    # 3. mint the Message provenance node + one FrameReading per hit.
    mid = _mint_message(agent, text, tick=tick, market=market)
    fr_nodes = []
    grounded_any = False
    for (symbol, motion) in hits:
        fr = sub.add_node("FrameReading",
                          {"symbol": symbol, "motion": motion, "market": market})
        try:
            native.add_edge_unchecked(fr, "is_frame_reading", fr)
        except TypeError:
            native.add_edge_unchecked(fr, "is_frame_reading", fr, {})
        # provenance: FrameReading -read_from-> Message (SensorAnchor-eligible).
        native.add_edge_unchecked(fr, "read_from", mid)
        fr_nodes.append(fr)
        grounded_any = True

    # H3 construction: a confident stance with NO real frame ground.
    forced_fr = None
    if confident_override is not None:
        symbol, motion, _sign = confident_override
        forced_fr = sub.add_node("FrameReading",
                                 {"symbol": symbol, "motion": motion,
                                  "market": market, "ungrounded_confident": 1})
        try:
            native.add_edge_unchecked(forced_fr, "is_frame_reading", forced_fr)
        except TypeError:
            native.add_edge_unchecked(forced_fr, "is_frame_reading", forced_fr, {})
        # DELIBERATELY no read_from edge -> no provenance to a Message/anchor.
        fr_nodes.append(forced_fr)

    # 4. run the ib_decode_stance RULE — the DECISION (which stance). The
    #    freshly-added FrameReading/CBSpeechAct nodes are dirty, so a small step
    #    budget fires the single Eq-join without an uncapped whole-graph fixpoint.
    native.run_rules(3)

    # 5. collect the StanceReadings this decode produced, marshal each into the
    #    reused belief-update primitive concept_apply_evidence (the SAME call
    #    reasoning_can_bridge.py:227 makes; the market's denotes edge + concept
    #    map were resolved ONCE at boot, so we apply directly on the cached
    #    Concept node here rather than re-running the full correspondence
    #    fixpoint per utterance — strict reuse of the primitive, not a fork).
    stances = []
    applied_concepts = {}
    for fr in fr_nodes:
        for sr in native.neighbours(fr, "decoded_to"):
            at = sub.node(sr)["attrs"]
            attr = at.get("attr")
            sign = int(at.get("sign", 0))
            stances.append({"attr": attr, "sign": sign,
                            "symbol": at.get("symbol"), "motion": at.get("motion"),
                            "stance_reading": sr, "frame_reading": fr})
            if sign == 0:
                continue
            # REUSE: apply the stance as CAN evidence on <stance>_stance_for:market.
            # The evidence CONFIRMS this stance (the utterance IS hawkish/dovish),
            # so it is always POSITIVE on the stance's own Concept; `sign` carries
            # the rates-band direction (read at step 8), not the evidence polarity.
            concept = mk["concepts"].get(attr)
            if concept is not None:
                native.concept_apply_evidence(concept, 1.0, alpha)
                applied_concepts[attr] = concept
            # provenance for grounding: StanceReading -grounded_in-> FrameReading
            # -grounded_in-> Message, but ONLY when the frame reading has a real
            # read_from Message (a genuine frame ground). The forced H3 reading
            # has no read_from, so it never gets an anchor edge. The Message is
            # anchored to a SensorAnchor once, below (a corpus utterance is bytes
            # ingested from outside the agent, the SensorAnchor shape).
            if native.neighbours(fr, "read_from"):
                native.add_edge_unchecked(sr, "grounded_in", fr)
                native.add_edge_unchecked(fr, "grounded_in", mid)

    # ensure the corpus Message is anchored (SensorAnchor) so a grounded chain
    # actually reaches an anchor. grounding_reach maps Message{source:'audio'};
    # a corpus Message is the same provenance shape — mint the anchor edge here
    # (mechanical, the SAME add-edge idiom ensure_grounding_edges uses).
    _anchor_corpus_message(agent, mid)

    # 6. relax the CAN network — GOTCHA: force_all_dirty BEFORE run_rules.
    #    Small step budget: the 3-state discrete update propagates external_field
    #    into state in ~2 steps (verified live); force_all_dirty dirties the
    #    whole 600-seed graph, so an uncapped fixpoint would needlessly re-run
    #    every unrelated rule. 3 steps is sufficient for the CAN update and keeps
    #    the per-utterance decode fast.
    native.force_all_dirty()
    native.run_rules(3)

    # 7. read the CAN marginal <sigma> per-frame (the graded signal).
    #    the winning stance = the target-scoped Concept with the largest
    #    POSITIVE state (the stance most confirmed by the utterance's evidence).
    #    The SELECTION is the held Argmax Term over the confirmed stance
    #    Concepts (graph-native, evaluated in Rust) — NOT a Python argmax loop.
    winner = native.evaluate(_winning_stance_term(market), {})
    if winner is None:
        return {"direction": "none", "marginal": 0.0, "grounding_weight": 0.0,
                "reached": False, "hops": None, "grounding_gap": False,
                "base_shift": 0.0, "shift": 0.0, "stances": stances,
                "frame_hits": hits}

    # map the winning Concept node back to its stance + marginal (mechanical
    # read-back off the graph — Python did not choose the winner).
    concept = winner
    marginal = float(sub.node(concept)["attrs"].get("state") or 0.0)
    winning_attr = sub.node(concept)["attrs"].get("name")
    stance = None
    for s in _STANCES:
        if frame._attr(s) == winning_attr:
            stance = s
            break

    # 8. direction from the winning (confirmed) stance's codebook sign — the
    #    rates-band direction of that stance. hawkish=+1 -> up, dovish=-1 ->
    #    down, neutral=0 -> none. The sign->direction mapping is CODEBOOK DATA
    #    (frame.SIGN_DIRECTION), copied graph-native onto each StanceReading's
    #    `direction` attr by the ib_decode_stance rule. Here we READ that graph
    #    datum off the winning stance's StanceReading — a mechanical graph read,
    #    NOT a Python if/elif that DECIDES the direction.
    direction = "none"
    for s in stances:
        if s["attr"] == frame._attr(stance):
            sr_dir = sub.node(s["stance_reading"])["attrs"].get("direction")
            if sr_dir is not None:
                direction = sr_dir
            break

    # 9. grounding_reach transitive read = confidence gate + weight.
    #    grounded chain: StanceReading -> FrameReading -> Message -> SensorAnchor.
    reached = False
    hops = None
    gap = False
    # check the winning stance's StanceReading provenance
    winning_srs = [s["stance_reading"] for s in stances
                   if s["attr"] == frame._attr(stance)]
    if winning_srs:
        greach = gr.grounding_reach(agent, winning_srs[0])
        reached = bool(greach["reached"])
        hops = greach["hops"]
    # the overconfidence guard: a confident (low-residual) stance that reached
    # no anchor mints a GroundingGap.
    if winning_srs and not reached:
        # flag the StanceReading as confident-but-ungrounded (residual/confidence
        # attrs the reused flag reads).
        sub.set_attr(winning_srs[0], "residual", 0.0)
        sub.set_attr(winning_srs[0], "confidence", 1.0)
        flagged = gr.flag_ungrounded_confident(
            agent, node_types=["StanceReading"])
        gap = winning_srs[0] in flagged

    # 10. grounding weight: 0 if the chain reached no anchor (GroundingGap ->
    #     shift ~0), else a graded weight = |marginal| discounted by hops.
    if not reached:
        grounding_weight = 0.0
    else:
        # closer to the anchor (fewer hops) = higher confidence; |marginal| is
        # the per-frame grounding-vector component (the CAN marginal IS the
        # grounding vector, seeds/causal_attitude_networks.json).
        hop_discount = 1.0 / (1.0 + (hops - 1 if hops else 0))
        grounding_weight = min(1.0, abs(marginal)) * hop_discount

    # 11. the band shift: base_shift (direction unit) x grounding_weight.
    base_shift = {"up": 1.0, "down": -1.0, "none": 0.0}[direction]
    shift = base_shift * grounding_weight

    return {"direction": direction, "marginal": marginal,
            "grounding_weight": grounding_weight, "reached": reached,
            "hops": hops, "grounding_gap": gap, "base_shift": base_shift,
            "shift": shift, "stance": stance, "concept": concept,
            "stances": stances, "frame_hits": hits}


def _anchor_corpus_message(agent, mid):
    """Mechanically mint Message -grounded_in-> SensorAnchor for a corpus
    Message, mirroring ensure_grounding_edges' audio-Message mapping (a corpus
    utterance is the same provenance shape: bytes ingested from outside the
    agent). Idempotent."""
    sub, native = _resolve(agent)
    # reuse the anchor singleton ensure_grounding_edges maintains.
    anchor = None
    for n in sub.nodes("SensorAnchor"):
        anchor = n
        break
    if anchor is None:
        anchor = sub.add_node("SensorAnchor", {"kind": "SensorAnchor"})
    if not sub.has_edge(mid, "grounded_in", anchor):
        native.add_edge_unchecked(mid, "grounded_in", anchor)


def reset_beliefs(agent, mk):
    """Zero the market's target-scoped stance Concepts between independent
    utterances (each snippet is a fresh read; belief does not carry across
    unrelated snippets in the per-snippet H1 measurement). Mechanical."""
    sub, native = _resolve(agent)
    for attr, c in mk["concepts"].items():
        sub.set_attr(c, "external_field", 0.0)
        sub.set_attr(c, "state", 0.0)
    native.force_all_dirty()
    native.run_rules(3)


__all__ = ["boot", "ensure_codebook_seed", "teach_codebook", "build_market",
           "decode_utterance", "reset_beliefs"]

"""reading_drive — THE GOAL-DRIVEN READING/ANALYSIS ADAPTER.

The Jabberwock is seeded with a GOAL ("produce a literary analysis of <source>")
and the source as I/O; the comprehension->analysis process then fires to a
`run_rules` FIXPOINT, driven by the goal + data-dependencies, and the analysis
emerges as graph state. This module is the THIN WORLD ADAPTER around that:

    run_reading_flow(agent, text, report=...)
      1. INGEST   — mint a `Source{text}` node (mechanical text->graph I/O).
      2. GOAL     — mint the report `Goal` (the ONLY instruction): a comprehend
                    goal (reading_report) or a produce-analysis goal (+produce_report).
      3. STAGES   — mint one `AnalysisStage{name,status:pending}` per faculty
                    (mechanical ingest, like question_driver._ingest_target mints
                    the Goal tree). NO order is imposed here.
      4. PUMP     — fire the `analysis_advance` reflex (advances ONE dispatched
                    stage via its Python shim) then run the seeded `la_dispatch_*`
                    rules to fixpoint (seeds/literary_analysis_driving.json). The
                    rules DISPATCH each stage the moment its OWN graph precondition
                    holds; the fixpoint sequences the faculties for free. There is
                    NO Python faculty sequence anywhere in this loop.
      5. READ-OFF — the accumulated blackboard (comprehension views) + the minted
                    `Claim` nodes are read back out mechanically.

The kind of sequencing that `comprehension_reader.read_and_comprehend` used to
impose as a hand-ordered Python list, and `literary_analysis.produce_analysis`
as a section-marshalling loop, is GONE — it lives in the seed's dispatch rules.
Each faculty is now a STAGE fired by a rule on its data-dependency, exactly as
seeds/shape_decode_loop.json's sd_* rules ARE the decode->grow->re-decode loop.

The stage SHIMS below are thin boundary invocations of the EXISTING faculties
(situation_model_reader / coref_entities / inference_generation /
discourse_coherence / global_monitoring / character_tom / narrative_structure /
trope_theme / literary_analysis) — each reused as-is; none reimplemented. A shim
runs its faculty and RE-READS ITS INPUTS FROM GRAPH NODES (the `_*_from_graph`
re-readers below) — NOTHING passes between stages through the Python blackboard.
Every inter-stage fact is graph-resident: the situation-model spine as
SmEntity/SmEvent, the per-sentence parse as `SentenceParse` nodes (raw + coref-
resolved predications), coherence pairs as `CoherencePair`, physical-causal
links as `CausalLink`, the goal-action backbone as `EnablingChain`, plus the
existing DiscourseEvent/NarrativeRole/Trope/Theme/Claim nodes and the additive
durable markers (`coref_number`/`sentence_order` on SmEvent, `blocked_gap` on
SmEntity, `need_attr` on the want-SmEvent, `schema` on the causal edge). This is
the ORDER-N PREREQUISITE: a nested story reads from ITS OWN subgraph, where a
flat Python dict could not nest. A shim STILL stashes its faculty's view onto
`adapter._master["analysis_bb"]`, but only as the RETURN BUFFER for
`comprehension_result`/`produce_analysis` — NO stage reads another stage's
output from it (proven by the poison-blackboard gate: wiping the view keys mid-
flow yields a byte-identical report, because every stage re-read from nodes).

`_advance_dispatched_stage` is the reflex RESPONSE — the I/O boundary, shaped
EXACTLY like world_adapter._question_pursue_advance / _enact_advance: it looks up
which shim the dispatched stage names and calls it, then marks the stage done. It
NEVER branches on graph state to choose a faculty (a lookup, not a decision).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_DSLPY = os.path.join(ROOT, "runners", "dsl", "python")
if _DSLPY not in sys.path:
    sys.path.insert(0, _DSLPY)

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from domains.reflective_faculty import _agent_root_node, _ensure_seed_chain  # noqa: E402


# --------------------------------------------------------------------------- #
#  The adapter facade — reuse WorldAdapter's reflex/tick machinery over an
#  EXISTING substrate (the _QDAdapter precedent, question_driver.py).
# --------------------------------------------------------------------------- #
class _LAAdapter(WorldAdapter):
    def __init__(self, s):
        self.s = s
        self.inner = getattr(s, "_inner", s)
        agent = _agent_root_node(s)
        if agent is None:
            agent = s.add_node("Agent", {})
        self.agent = agent
        self._master_state = None
        # THE FLOW IDENTITY (Wave 1A, the stale-Source fix). One `run_reading_
        # flow` call = one flow; `flow` is set to THIS call's own `Source` node
        # id right after it is minted, and threaded (as the pre-existing `unit`
        # scoping convention nested_reading.py already uses for StoryUnit
        # isolation) into every faculty call and graph re-reader below, so a
        # SECOND flow on the SAME persistent substrate never reads or mutates
        # the FIRST flow's nodes. `flow=None` (unset) is the byte-identical
        # legacy/global case: `run_produce_over_graph` (reads an ALREADY-BUILT
        # whole-graph comprehension view by design) and `run_nested_reading_
        # flow` (its own StoryUnit `unit` scoping) both leave it unset.
        self.flow = None


def _bb(ad) -> dict:
    return ad._master["analysis_bb"]


# --------------------------------------------------------------------------- #
#  THE GRAPH RE-READERS — one pure graph query per inter-stage input. Each
#  reconstructs a faculty view from graph NODES (never the Python blackboard):
#  the blackboard's inter-stage role is dissolved. All read `ad.s` only.
# --------------------------------------------------------------------------- #
def _vv(n):
    return n.value if hasattr(n, "value") else n


def _resolve_node_by_value(ad, node_type: str, value) -> Optional[Any]:
    """Resolve a PLAIN value id (stored via `_vv`, JSON-safe — the convention
    every flow-scoped attr uses) back to the real NodeID of the matching
    `node_type` node. Mechanical graph lookup, the twin of `_shim_spine`'s own
    `ev_node = {_vv(n): n for n in ...}` dict — used here for the ring-buffer
    `trace_node` provenance (Wave: dynamic-thresholds/reopen), which must be a
    JSON-embeddable scalar in `establish_meta` but a real NodeID once
    `reading_scope.reactivate` dereferences it via `sub.node(...)`."""
    if value is None:
        return None
    for n in ad.s.nodes(node_type):
        if _vv(n) == value:
            return n
    return None


def _source_text(ad) -> Optional[str]:
    """THIS FLOW's own source text (Wave 1A fix): an O(1) direct read of
    `ad._flow_node` (the flow's own Source node, the raw NodeID `run_reading_
    flow` stashed for exactly this) when set — never "the first Source node
    ever minted on the substrate", which is what let every flow on a
    persistent substrate silently re-read flow #1's text forever. Unset (the
    legacy/global adapters — `run_produce_over_graph`, `run_nested_reading_
    flow`) falls back to the prior first-Source scan, byte-identical for
    those callers."""
    fnode = getattr(ad, "_flow_node", None)
    if fnode is not None:
        node = ad.s.node(fnode)
        return node["attrs"].get("text") if node is not None else None
    for n in ad.s.nodes("Source"):
        return ad.s.node(n)["attrs"].get("text")
    return None


def _sentences_from_graph(ad) -> list:
    from domains import reading_collapse as rc
    text = _source_text(ad)
    return rc._split_sentences(text) if text else []


def _sm_entity_node(ad, name):
    flow = getattr(ad, "flow", None)
    for n in ad.s.nodes("SmEntity"):
        at = ad.s.node(n)["attrs"]
        if at.get("name") == name and (flow is None or at.get("unit") == flow):
            return n
    return None


def _situation_model_from_graph(ad) -> dict:
    """FLOW-SCOPED (Wave 1A): only THIS flow's own SmEntity nodes (`ce.
    read_into_situation_model` is called with `unit=ad.flow` from `_shim_spine`,
    so every entity it mints carries a matching `unit` attr) — a second flow's
    entities never bleed into this one's situation model. `ad.flow` unset is
    the byte-identical legacy (whole-graph) read. `unit` (like `name`) is node-
    identity BOOKKEEPING, not a semantic fact about the entity — it is stripped
    from the per-entity view returned here (the SAME instance-specific-id
    exclusion `name` already gets), so two independently-booted agents reading
    the SAME text still compare byte-identical (the id itself is never
    meaningful outside this substrate)."""
    flow = getattr(ad, "flow", None)
    model: dict = {}
    for n in ad.s.nodes("SmEntity"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("unit") != flow:
            continue
        nm = at.get("name")
        if nm:
            model[nm] = {k: v for k, v in at.items() if k not in ("name", "unit")}
    return model


def _sentence_parse_rows(ad) -> list:
    """The durable `SentenceParse` nodes (minted by the spine stage), sorted by
    order — each carries the sentence's RAW predications (the textbase) and its
    coref-RESOLVED predications (the ingest inputs). FLOW-SCOPED (Wave 1A): only
    THIS flow's own rows (`flow` attr == `ad.flow`, stamped by `_mint_sentence_
    parses`) — a persistent substrate's SentenceParse nodes from earlier flows
    are never re-read, which is both the stale-Source correctness fix (order 0
    of THIS flow's own text, not order 0 of whichever flow ran first) and the
    O(turns) -> O(this-flow's-own-sentences) cost fix. `ad.flow` unset is the
    byte-identical legacy (whole-graph) read."""
    flow = getattr(ad, "flow", None)
    rows = []
    for n in ad.s.nodes("SentenceParse"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        rows.append((at.get("order"), at))
    rows.sort(key=lambda r: (r[0] if r[0] is not None else -1))
    return [at for _, at in rows]


def _textbase_from_graph(ad) -> list:
    """The textbase re-reader: per-sentence RAW predication list, off the
    durable SentenceParse nodes. No re-parse of Source.text."""
    out = []
    for at in _sentence_parse_rows(ad):
        out.append({"sentence": at.get("sentence"),
                    "predications": json.loads(at.get("raw_predications") or "[]"),
                    "source": at.get("source")})
    return out


def _ingests_from_graph(ad) -> list:
    """The flat, in-order per-predication ingest list, shaped exactly as
    `comprehension_reader._mint_goal_action_enabling_chain` consumes it (one
    record per predication carrying the coref-RESOLVED `predication`), re-read
    off the SentenceParse nodes' resolved predications."""
    out = []
    for at in _sentence_parse_rows(ad):
        for p in json.loads(at.get("resolved_predications") or "[]"):
            out.append({"predication": p})
    return out


def _goal_from_graph(ad) -> list:
    """The minted goal records, off the want-SmEvents inference_generation.
    resolve_goal_gap mints (verb='want', surface='implicit_need'):
    idx_protagonist->entity, idx_intentionality->remedy, need_attr->the
    triggering need-state, plus the entity's own SmEntity node. FLOW-SCOPED
    (Wave 1A): `unit` is stamped on every want-SmEvent because `_shim_infer_goal`
    calls `resolve_goal_gap(..., unit=ad.flow)`."""
    flow = getattr(ad, "flow", None)
    goals = []
    for n in ad.s.nodes("SmEvent"):
        at = ad.s.node(n)["attrs"]
        if at.get("verb") != "want" or at.get("surface") != "implicit_need":
            continue
        if flow is not None and at.get("unit") != flow:
            continue
        entity = at.get("idx_protagonist")
        goals.append({"minted": True,
                      "gap": {"entity": entity, "need_attr": at.get("need_attr"),
                              "node": _sm_entity_node(ad, entity)},
                      "supplies": {"remedy": at.get("idx_intentionality")}})
    return goals


def _discourse_pairs_from_graph(ad) -> list:
    """The decoded coherence pairs, off the durable `CoherencePair` nodes the
    discourse stage mints (the Python substrate exposes no edge-attr reader, so
    the pair's `relation`/i/j live on a node). The narrative stage reads these
    only for the 'contrast' relation. FLOW-SCOPED (Wave 1A) via the `flow` attr
    `_mint_coherence_pairs` stamps."""
    flow = getattr(ad, "flow", None)
    pairs = []
    for n in ad.s.nodes("CoherencePair"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        pairs.append({"relation": at.get("relation"), "i": at.get("i"), "j": at.get("j")})
    return pairs


def _discourse_nodes_from_graph(ad) -> list:
    """FLOW-SCOPED (Wave 1A): `unit` is stamped on every DiscourseEvent because
    `_shim_discourse` calls `dc.read_discourse(..., unit=ad.flow)`."""
    flow = getattr(ad, "flow", None)
    out = []
    for n in ad.s.nodes("DiscourseEvent"):
        if flow is not None and ad.s.node(n)["attrs"].get("unit") != flow:
            continue
        out.append(_vv(n))
    return out


def _causal_from_graph(ad) -> list:
    """The physical-causal records, off the durable `CausalLink` nodes the
    infer_causal stage mints (i = the solution sentence's order, schema = the
    winning physical-effect schema). trope_theme's INDIRECT signal reads these.
    FLOW-SCOPED (Wave 1A) via the `flow` attr `_mint_causal_links` stamps."""
    flow = getattr(ad, "flow", None)
    out = []
    for n in ad.s.nodes("CausalLink"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        out.append({"minted": True, "gap": {"i": at.get("i"), "j": at.get("j")},
                    "schema": at.get("schema")})
    return out


def _enabling_chain_from_graph(ad) -> list:
    """The goal-action backbone, off the durable `EnablingChain` nodes the
    enabling stage mints (entity, goal_sentence, action_sentences). FLOW-SCOPED
    (Wave 1A) via the `flow` attr `_mint_enabling_chains` stamps."""
    flow = getattr(ad, "flow", None)
    rows = []
    for n in ad.s.nodes("EnablingChain"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        rows.append({"entity": at.get("entity"),
                     "goal_sentence": at.get("goal_sentence"),
                     "action_sentences": json.loads(at.get("action_sentences") or "[]")})
    return rows


def _centrality_from_graph(ad) -> dict:
    from domains import discourse_coherence as dc
    return dc.centrality_ranking(ad, unit=getattr(ad, "flow", None))


def _narrative_arc_from_graph(ad) -> dict:
    """The story-grammar arcs, reconstructed off the minted `NarrativeRole`
    nodes (one arc per EnablingChain entity, roles via
    `narrative_structure.read_narrative_roles`) + the goal (remedy). trope +
    produce consume this; both only read entity + role/order, which the minted
    NarrativeRole nodes carry. FLOW-SCOPED (Wave 1A): `unit=ad.flow` confines
    `read_narrative_roles` to this flow's own NarrativeRole nodes."""
    from domains import narrative_structure as ns
    flow = getattr(ad, "flow", None)
    goals = {g["gap"]["entity"]: g for g in _goal_from_graph(ad)}
    arcs = []
    for chain in _enabling_chain_from_graph(ad):
        entity = chain.get("entity")
        g = goals.get(entity)
        remedy = (g.get("supplies") or {}).get("remedy") if g else None
        arcs.append({"entity": entity, "goal_sentence": chain.get("goal_sentence"),
                     "remedy": remedy, "roles": ns.read_narrative_roles(ad, entity, unit=flow)})
    return {"arcs": arcs}


def _trope_theme_from_graph(ad) -> dict:
    """The trope/theme results, reconstructed off the minted `Trope`/`Theme`
    nodes (produce consumes tropes + theme; it never reads the decode-time
    tokens/residual, which stay in the return buffer). FLOW-SCOPED (Wave 1A):
    `tt.recognize_tropes_and_theme` (called with `unit=ad.flow` from
    `_shim_trope`) already stamps `unit` on every Trope/Theme it mints."""
    from domains import trope_theme as tt
    sub = ad.s
    flow = getattr(ad, "flow", None)
    entities = []
    for nt in ("Trope", "Theme"):
        for n in sub.nodes(nt):
            at = sub.node(n)["attrs"]
            if flow is not None and at.get("unit") != flow:
                continue
            e = at.get("entity")
            if e is not None and e not in entities:
                entities.append(e)
    results = []
    for entity in entities:
        tropes = []
        for n in sub.nodes("Trope"):
            at = sub.node(n)["attrs"]
            if at.get("entity") != entity:
                continue
            if flow is not None and at.get("unit") != flow:
                continue
            tropes.append({"entity": entity, "name": at.get("name"),
                           "covered_tokens": list(at.get("covered_tokens") or []),
                           "shape_fit": at.get("shape_fit"), "theme": at.get("theme"),
                           "label": {"name": at.get("label_name"),
                                     "source": at.get("label_source"),
                                     "definition": at.get("label_definition")},
                           "_node_obj": n, "node": _vv(n)})
        theme = None
        tn = tt._existing_theme(sub, entity, unit=flow)
        if tn is not None:
            tat = sub.node(tn)["attrs"]
            theme = {"entity": entity, "minted": True, "node": _vv(tn),
                     "lines": list(tat.get("lines") or []),
                     "tropes": list(tat.get("tropes") or [])}
        results.append({"entity": entity, "tropes": tropes, "theme": theme})
    return {"results": results}


def _comprehension_view_from_graph(ad) -> dict:
    """The comprehension view, reconstructed ENTIRELY from graph nodes — the
    input the trope + produce stages read (replacing `_comprehension_view(bb)`).
    Every field is a pure graph query; the Python blackboard is not consulted."""
    from domains import inference_generation as ig
    return {
        "text": _source_text(ad),
        "sentences": _sentences_from_graph(ad),
        "spine": {"textbase": _textbase_from_graph(ad),
                  "ingests": _ingests_from_graph(ad),
                  "situation_model": _situation_model_from_graph(ad)},
        "goal": _goal_from_graph(ad),
        "goal_gaps": ig.detect_goal_gaps(ad, unit=getattr(ad, "flow", None)),
        "centrality": _centrality_from_graph(ad),
        "causal": _causal_from_graph(ad),
        "discourse": {"pairs": _discourse_pairs_from_graph(ad),
                      "nodes": _discourse_nodes_from_graph(ad)},
        "enabling_chain": _enabling_chain_from_graph(ad),
        "narrative_arc": _narrative_arc_from_graph(ad),
        "trope_theme": _trope_theme_from_graph(ad),
    }


# --------------------------------------------------------------------------- #
#  THE STAGE SHIMS — each a thin boundary invocation of an existing faculty +
#  a stash of that faculty's own view onto the blackboard. Reused verbatim from
#  the (now-deleted) read_and_comprehend / produce_analysis step bodies.
# --------------------------------------------------------------------------- #
def _mint_sentence_parses(ad, spine) -> None:
    """MECHANICAL I/O: mint one durable `SentenceParse` node per sentence
    holding the RAW predications (textbase) and the coref-RESOLVED predications
    (the ingest inputs), and stamp each change-of-state SmEvent's
    `sentence_order`. This makes the per-sentence parse + the plural-affected-
    entity mapping graph-readable WITHOUT re-parsing Source.text — the textbase
    ledger's 'mint raw-predication nodes' path (cheaper + idempotent-safe vs a
    read-only re-parse; disclosed cost: N SentenceParse nodes, one per
    sentence, each carrying two JSON predication lists).

    DYNAMIC-THRESHOLDS (Wave: 2026-07-11): also carries the per-sentence
    COMPLEXITY measurements `coref_entities.read_into_situation_model` already
    computed (`residual_marker_count`/`swallowed_ratio`, mechanical — the
    `reform_overcomplex_clause` rule's own thresholds compare against these)
    and the sentence's own ring-buffer `trace_node` (so `_shim_monitoring` can
    look up the RIGHT prior trace for a warm reopen without re-deriving it —
    the SAME provenance `reading_and_monitor`'s Python `established_by` dict
    keeps ephemerally, now persisted as graph data). A self-loop `is_sentence_
    parse` edge (mirrors salient_cache.py's `is_scell` — "single-node rule
    matching") lets a graph RULE match+act on ONE SentenceParse at a time."""
    from domains import reading_collapse as rc
    flow = getattr(ad, "flow", None)
    textbase = spine.get("textbase") or []
    ingests = spine.get("ingests") or []
    ev_node = {_vv(n): n for n in ad.s.nodes("SmEvent")
               if flow is None or ad.s.node(n)["attrs"].get("unit") == flow}
    cum = 0
    for order, tb in enumerate(textbase):
        preds = tb.get("predications") or []
        recs = ingests[cum:cum + len(preds)]
        cum += len(preds)
        resolved = [list(r.get("predication") or []) for r in recs]
        sp_attrs = {"order": order, "sentence": tb.get("sentence"), "source": tb.get("source"),
                    "raw_predications": json.dumps(preds),
                    "resolved_predications": json.dumps(resolved),
                    "residual_marker_count": float(tb.get("residual_marker_count") or 0.0),
                    "swallowed_ratio": float(tb.get("swallowed_ratio") or 0.0)}
        tn = tb.get("trace_node")
        if tn is not None:
            sp_attrs["trace_node"] = _vv(tn)
        if flow is not None:
            sp_attrs["flow"] = flow
        sp = ad.s.add_node("SentenceParse", sp_attrs)
        ad.inner.add_edge_unchecked(sp, "is_sentence_parse", sp)   # single-node rule matching
        # CLAUSE STRUCTURE AS GRAPH DATA (2026-07-12): persist the parser's
        # clause recognition (`reading_collapse.decompose_sentence` -- the
        # clause recogniser, same parser class as read_clause, read-only) as
        # one `ClauseParse` node per recognised clause, edged `sp -has_clause->
        # cp`. Mechanical ingest, the clause twin of word tokenization -- it
        # makes a run-on sentence's clauses first-class graph state the
        # meaning_inference re-read stage (and any future rule) can iterate,
        # instead of re-decomposing in Python. A single-clause sentence yields
        # exactly one ClauseParse (== the sentence).
        #
        # The clause is stored as its LATTICE-DECODED WORD-LIST (`clause_words`,
        # JSON) -- the words comprehend_text._recognise_regions already
        # recognised graph-natively (lattice decode over the held lexicon, the
        # byte-parity-critical tokenizer). The re-read stage feeds this list
        # STRAIGHT into read_clause's word-list path (the decompose/parity
        # path, `read_clause(clause=[...])`) so tokenization happens ONCE and
        # is never re-run on a re-joined string. `clause_text` is a display-only
        # mirror.
        sent_txt = tb.get("sentence")
        if sent_txt:
            clauses = (rc.decompose_sentence(ad, sent_txt) or {}).get("clauses") or []
            for ci, cl in enumerate(clauses):
                words = [str(w) for w in cl if str(w).strip()]
                if not words:
                    continue
                cp_attrs = {"order": ci, "clause_words": json.dumps(words),
                            "clause_text": " ".join(words)}
                if flow is not None:
                    cp_attrs["flow"] = flow
                cp = ad.s.add_node("ClauseParse", cp_attrs)
                ad.inner.add_edge_unchecked(sp, "has_clause", cp)
        for r in recs:
            ev = r.get("event")
            if ev is not None and ev in ev_node:
                ad.s.set_attr(ev_node[ev], "sentence_order", order)


def _supersede_spine(ad) -> None:
    """FOVEATION-AS-HINT (2026-07-11): clear THIS flow's own spine-produced
    SmEntity/SmEvent/SentenceParse nodes before a re-collapse at a WIDER
    aperture — mirrors `_supersede_order_n`'s clear-then-recompute discipline,
    extended to the (normally one-shot, first-pass) spine stage for the ONE
    case it must re-collapse: an `escalate_truncated_read` rule (seeds/
    reading_aperture.json) widened `max_sentences_override` on the flow's own
    Source node — graph data, never a Python decision — and re-minted a
    'spine' AnalysisStage. Re-running `read_into_situation_model` WITHOUT
    superseding first would re-ingest sentences [0:old_cap] a second time,
    duplicating entities/events; superseding makes the re-collapse a clean
    full re-read over [0:new_cap], exactly as if that cap had been the
    aperture from the start. Flow-scoped: a persistent substrate's OTHER
    flows are untouched. SmMention carries no unit/flow attr (see the
    pronoun-enrichment precedent) so it is deliberately left alone — an
    honest, documented residual (the coref resolution TRACE accumulates
    across a re-collapse; the SmEntity model it fed does not)."""
    flow = getattr(ad, "flow", None)
    if flow is None:
        return
    for t in ("SmEntity", "SmEvent"):
        for n in list(ad.s.nodes(t)):
            if ad.s.node(n)["attrs"].get("unit") != flow:
                continue
            ad.inner.remove_node(n)
    for t in ("SentenceParse", "ClauseParse"):
        for n in list(ad.s.nodes(t)):
            if ad.s.node(n)["attrs"].get("flow") != flow:
                continue
            ad.inner.remove_node(n)


def _shim_spine(ad) -> None:
    from domains import dictionary_lexicon as dl
    from domains import coref_entities as ce
    bb = _bb(ad)
    dl.warm_wordnet("en")
    text = _source_text(ad)                        # INPUT off the Source node
    # FOVEATION-AS-HINT (2026-07-11): the flow's Source node may carry a
    # `max_sentences_override` — an escalation rule's own graph data (never a
    # Python decision) widening the aperture past this flow's original
    # `max_sentences` hint. `bb.get("max_sentences")` stays the byte-identical
    # default for every flow no escalation rule ever touched.
    fnode = getattr(ad, "_flow_node", None)
    src_attrs = ad.s.node(fnode)["attrs"] if fnode is not None else {}
    override = src_attrs.get("max_sentences_override")
    ms = int(override) if override is not None else bb.get("max_sentences", 40)
    if override is not None and src_attrs.get("sentences_read") is not None:
        # RE-COLLAPSE: this flow's spine already ran once (sentences_read was
        # already stamped below) and an escalation rule just widened the cap —
        # supersede the prior spine output so this collapse recomputes cleanly
        # over the WIDER text, then sync the flow's own working aperture
        # (`bb["max_sentences"]`) so any FIRST-PASS stage that reads it LATER
        # in this same flow (discourse, ...) also sees the widened cap.
        # KNOWN RESIDUAL: a first-pass stage that already ran BEFORE this
        # escalation fired (discourse/infer_goal/... on a full-stage document
        # flow, as opposed to the spine-only conversational aperture) does
        # NOT itself re-collapse this wave — only spine (and, via the
        # existing input_epoch/coh_epoch growth-triggered rearm, the order-N
        # narrative/trope/monitoring stages) automatically widen.
        _supersede_spine(ad)
        bb["max_sentences"] = ms
    # SPINE: situation_model_reader (mint SmEntity/SmEvent + fixpoint, inside)
    # then coref_entities (bind pronouns) — one whole-text driver. `unit=ad.flow`
    # (Wave 1A) is the SAME StoryUnit-isolation convention nested_reading.py uses,
    # reused here to isolate ONE flow's entities from another's on a persistent
    # substrate. `flow_node`/`register` (Wave: dynamic-thresholds, 2026-07-11):
    # mechanical passthrough so the LIVE per-sentence ring buffer inside
    # read_into_situation_model can bound itself to THIS flow's own EFFECTIVE
    # capacity (domains/reading_norms) and record eviction pressure back onto
    # this flow's own Source node.
    from domains import reading_norms as rn
    spine = ce.read_into_situation_model(ad, text, max_sentences=ms,
                                         unit=getattr(ad, "flow", None),
                                         flow_node=fnode,
                                         register=rn.flow_register(ad.s, getattr(ad, "flow", None)))
    if fnode is not None:
        # TRUNCATION IS A DATUM (Wave: foveation-as-hint, task 1): pure
        # counting, mechanical — `sentences_total` is the FULL, untruncated
        # `_split_sentences` count; `sentences_read` is how many of them THIS
        # collapse actually read. Stamped on the flow's own Source node (O(1)
        # access via `ad._flow_node`), never a Python literal an escalation
        # rule could not see.
        total = len(_sentences_from_graph(ad))
        ad.s.set_attr(fnode, "sentences_total", float(total))
        ad.s.set_attr(fnode, "sentences_read", float(min(ms, total)))
    if getattr(ad, "flow", None) is not None:
        # `unit` is node-identity BOOKKEEPING (an instance-specific Source node
        # id), not a semantic fact — strip it from the RETURNED per-entity view
        # (the SAME treatment `_situation_model_from_graph` gives it) so two
        # independently-booted agents reading the same text still compare
        # byte-identical on `situation_model` (the id is meaningless outside
        # this substrate; it is only needed internally, already stamped on the
        # SmEntity graph node itself for `_situation_model_from_graph`'s filter).
        for ent_attrs in (spine.get("situation_model") or {}).values():
            ent_attrs.pop("unit", None)
    _mint_sentence_parses(ad, spine)               # graph-resident textbase/ingests
    bb["spine"] = spine                            # return buffer only
    bb["textbase"] = spine["textbase"]
    bb["sentences"] = _sentences_from_graph(ad)


def _shim_infer_goal(ad) -> None:
    from domains import inference_generation as ig
    bb = _bb(ad)
    flow = getattr(ad, "flow", None)
    ig.ensure_seeds(ad)
    textbase = _textbase_from_graph(ad)            # INPUT off SentenceParse nodes
    # GOAL-FROM-STATE + precondition + bridging inference — reads the situation
    # model. `unit=flow` (Wave 1A) throughout: a persistent substrate's earlier
    # flows never contribute a spurious gap/candidate to THIS flow's pass.
    goal_gaps = ig.detect_goal_gaps(ad, unit=flow)
    bb["goal_gaps"] = goal_gaps
    bb["goal"] = [ig.resolve_goal_gap(ad, g, unit=flow) for g in goal_gaps]
    precondition_gaps = ig.detect_precondition_gaps(ad, unit=flow)
    bb["precondition_gaps"] = precondition_gaps
    bb["blocking"] = [ig.resolve_precondition_gap(ad, g, t=900 + i, unit=flow)
                      for i, g in enumerate(precondition_gaps)]
    bridging_gaps = ig.detect_bridging_gaps(ad, textbase, unit=flow)
    bb["bridging_gaps"] = bridging_gaps
    bb["bridging"] = [ig.resolve_bridging_gap(ad, g, unit=flow) for g in bridging_gaps]
    bb["elaborative_candidates"] = ig.detect_elaborative_candidates(ad, unit=flow)


def _mint_coherence_pairs(ad, discourse) -> None:
    """MECHANICAL I/O: mint a durable `CoherencePair{i,j,relation}` per decoded
    pair (the Python substrate exposes no edge-attr reader, so the relation
    lives on a node the narrative stage can re-read). FLOW-SCOPED (Wave 1A):
    stamps `flow` so `_discourse_pairs_from_graph` reads back only this flow's
    own pairs."""
    flow = getattr(ad, "flow", None)
    for p in discourse.get("pairs") or []:
        rel = p.get("relation")
        if rel is not None:
            attrs = {"i": p.get("i"), "j": p.get("j"), "relation": rel}
            if flow is not None:
                attrs["flow"] = flow
            ad.s.add_node("CoherencePair", attrs)


def _shim_discourse(ad) -> None:
    from domains import discourse_coherence as dc
    bb = _bb(ad)
    dc.ensure_codebook(ad)
    text = _source_text(ad)                        # INPUT off the Source node
    # build the DiscourseEvent graph + coherence relations (centrality NOT yet).
    # `unit=ad.flow` (Wave 1A) stamps every minted DiscourseEvent with this
    # flow's own identity (the SAME convention nested_reading.py uses).
    discourse = dc.read_discourse(ad, text, window=bb.get("window", 2),
                                  max_sentences=bb.get("max_sentences", 40),
                                  unit=getattr(ad, "flow", None))
    _mint_coherence_pairs(ad, discourse)           # graph-resident pairs
    bb["discourse"] = discourse


def _mint_causal_links(ad, causal) -> None:
    """MECHANICAL I/O: mint a durable `CausalLink{i,j,schema}` per MINTED
    physical-causal record (trope_theme's INDIRECT signal re-reads it).
    FLOW-SCOPED (Wave 1A): stamps `flow` so `_causal_from_graph` reads back
    only this flow's own links."""
    flow = getattr(ad, "flow", None)
    for rec in causal or []:
        if not rec.get("minted"):
            continue
        gap = rec.get("gap") or {}
        attrs = {"i": gap.get("i"), "j": gap.get("j"), "schema": rec.get("schema")}
        if flow is not None:
            attrs["flow"] = flow
        ad.s.add_node("CausalLink", attrs)


def _shim_infer_causal(ad) -> None:
    from domains import inference_generation as ig
    bb = _bb(ad)
    flow = getattr(ad, "flow", None)
    textbase = _textbase_from_graph(ad)            # INPUT
    # PHYSICAL-CAUSAL: the DiscourseEvent graph now exists, so resolve_causal_gap
    # mints the `causes` edge instead of deferring. `unit=flow` (Wave 1A) confines
    # the DiscourseEvent lookup to this flow's own nodes.
    causal_gaps = ig.detect_causal_gaps(ad, textbase)
    bb["causal_gaps"] = causal_gaps
    causal = [ig.resolve_causal_gap(ad, g, unit=flow) for g in causal_gaps]
    _mint_causal_links(ad, causal)                 # graph-resident causal records
    bb["causal"] = causal


def _mint_enabling_chains(ad, chains) -> None:
    """MECHANICAL I/O: mint a durable `EnablingChain` per chain (entity /
    goal_sentence / action_sentences) — the goal-action backbone the narrative +
    trope + produce stages re-read (no edge-attr reader exists for `enables`).
    FLOW-SCOPED (Wave 1A): stamps `flow` so `_enabling_chain_from_graph` reads
    back only this flow's own chains."""
    flow = getattr(ad, "flow", None)
    for c in chains or []:
        attrs = {"entity": c.get("entity"),
                 "action_sentences": json.dumps(c.get("action_sentences") or [])}
        gs = c.get("goal_sentence")
        if gs is not None:
            attrs["goal_sentence"] = gs
        if flow is not None:
            attrs["flow"] = flow
        ad.s.add_node("EnablingChain", attrs)


def _shim_enabling(ad) -> None:
    from domains.comprehension_reader import _mint_goal_action_enabling_chain
    bb = _bb(ad)
    # GOAL-ACTION ENABLING CHAIN (Trabasso & van den Broek backbone) over the
    # DiscourseEvent graph, reusing the goal + sentence order — INPUTS off graph.
    # `unit=ad.flow` (Wave 1A) confines the DiscourseEvent-by-order lookup inside
    # to this flow's own nodes (sentence orders otherwise collide across flows).
    chain = _mint_goal_action_enabling_chain(
        ad, _textbase_from_graph(ad), _ingests_from_graph(ad), _goal_from_graph(ad),
        unit=getattr(ad, "flow", None))
    _mint_enabling_chains(ad, chain)               # graph-resident chains
    bb["enabling_chain"] = chain


def _shim_centrality(ad) -> None:
    bb = _bb(ad)
    # CENTRALITY: a pure graph read (Argmax over the weighted degree Term).
    bb["centrality"] = _centrality_from_graph(ad)


def _shim_monitoring(ad) -> None:
    from domains import global_monitoring as gm
    from domains import coref_entities as ce
    from domains import reading_collapse as rc
    from domains import reading_norms as rn
    from domains import reading_review as rr
    bb = _bb(ad)
    flow = getattr(ad, "flow", None)
    fnode = getattr(ad, "_flow_node", None)
    register = rn.flow_register(ad.s, flow)
    gm.ensure_seeds(ad)
    # STATEFUL kin-validation (the GLOBAL coherence check) — process each of THIS
    # FLOW's OWN SentenceParse nodes EXACTLY ONCE, marked with a durable
    # `kin_monitored` stamp. This is the executive cortex's non-sequitur detector:
    # a resolved kinship entailment is VALIDATED against the accumulated situation
    # model (gm.validate_against_model — the DECISION is the seeded
    # global_contradiction Program, not Python), minting a GlobalIncoherence flag
    # on a far-apart contradiction. That flag is what arms the order-N re-collapse
    # (la_rearm_narrative/la_rearm_trope read coh_epoch < Count(GlobalIncoherence),
    # itself flow-scoped in the seed — Wave 1A). The once-per-sentence guard is
    # essential: validate MUTATES the model, so a naive re-run on monitoring's own
    # re-collapse would flip-flop the established value and mint duplicate flags —
    # never reaching steady state. New sentences (an incremental feed) are
    # validated when they first arrive. FLOW-SCOPED (Wave 1A): filtering to this
    # flow's own SentenceParse rows FIRST is also the O(turns) -> O(this-flow's-
    # own-sentences) cost fix — a persistent substrate's accumulated rows from
    # earlier flows are never even inspected here.
    #
    # DYNAMIC-THRESHOLDS (Wave: 2026-07-11) — TWO ADDITIONS to this SAME
    # once-per-row loop, both mechanical shim execution of a decision already
    # made elsewhere (the _enact_advance precedent: evaluate a flag, apply it,
    # never decide):
    #   (a) THE REOPEN: a fired contradiction ESCALATES via gm.escalate_reread
    #       against the RIGHT prior establisher (gm.validate_against_model's own
    #       `prior_establisher` provenance, persisted on the SmEntity — never
    #       silently accepted, mirrors read_and_monitor's already-accepted
    #       live-call shape). Warm (reactivate a still-resident retained trace)
    #       beats cold (_reread_from_source) automatically — the trace's own
    #       evicted/resident flags (bounded by the ring in coref_entities.
    #       read_into_situation_model) decide that, not this shim.
    #   (b) THE REFORM: a SentenceParse the reform_overcomplex_clause RULE
    #       already marked `reform_pending` (its own residual/swallowed
    #       measurements crossed this flow's held threshold) gets its component
    #       structure decomposed via reading_collapse.read_clause_order_n, at
    #       this flow's own EFFECTIVE max_order (domains/reading_norms).
    for n in ad.s.nodes("SentenceParse"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        if at.get("kin_monitored") != 1:
            sentence = at.get("sentence")
            order = at.get("order")
            trace_node = at.get("trace_node")
            for turn, p in enumerate(json.loads(at.get("resolved_predications") or "[]"), start=1):
                kin = gm.kin_signal(ad, p, turn, unit=flow)
                if kin is not None and kin.get("resolved"):
                    ce._touch_entity(ad, sentence, kin["possessor"], "agent", turn, unit=flow)
                    chk = gm.validate_against_model(
                        ad, kin["possessor"], kin["entailed_attr"], kin["entailed_value"],
                        sentence=sentence, turn=turn, unit=flow,
                        sentence_order=order, trace_node=trace_node)
                    if chk["contradiction"]:
                        est = chk.get("prior_establisher")
                        if est is not None:
                            # `est["trace_node"]` is the ring-buffer trace's PLAIN
                            # value id (JSON-safe, stored via `_vv` — the SAME
                            # convention every other flow-scoped attr uses); resolve
                            # it back to the real NodeID `reactivate`/`_trace_
                            # resident` need to dereference (`sub.node(...)`).
                            est = dict(est)
                            est["trace_node"] = _resolve_node_by_value(
                                ad, "RetainedTrace", est.get("trace_node"))
                        max_revisits = rn.effective_max_revisits(ad, register)
                        gm.escalate_reread(ad, est, {"sentence": sentence}, p,
                                           max_revisits=max_revisits)
            ad.s.set_attr(n, "kin_monitored", 1)
    # THE REFORM (opportunistic same-pass catch — see _execute_pending_reforms's
    # own docstring for why a SECOND, ALWAYS-ON reflex is also registered as the
    # guaranteed catch-all: the monitoring stage's own one-shot dispatch can
    # settle to 'done' before reform_overcomplex_clause's rule-fixpoint pass
    # makes reform_pending visible).
    _execute_pending_reforms(ad)
    _execute_pending_reform_ingests(ad)
    # the monitoring VIEW (return buffer only; recomputed each collapse, harmless).
    monitoring = []
    for tb in _textbase_from_graph(ad):            # INPUT (already flow-scoped)
        preds = tb["predications"]
        local_incoherence = rr.combined_incoherence(ad, {"predications": preds})
        kins = [gm.kin_signal(ad, p, i, unit=flow) for i, p in enumerate(preds, start=1)]
        monitoring.append({"sentence": tb["sentence"], "predications": preds,
                           "local_incoherence": local_incoherence,
                           "kin_signals": [k for k in kins if k is not None]})
    bb["monitoring"] = monitoring


def _execute_pending_reforms(ad) -> None:
    """THE REFORM EXECUTOR (Wave: dynamic-thresholds/reform, 2026-07-11) — the
    _enact_advance precedent: MECHANICALLY apply a decision a graph RULE
    (reform_overcomplex_clause, seeds/reading_aperture.json) already made,
    never decide anything itself. For every `reform_pending=1, reform_done!=1`
    SentenceParse (flow-scoped when `ad.flow` is set): run reading_collapse.
    read_clause_order_n at this flow's own EFFECTIVE max_order (domains/
    reading_norms — deepens once this flow has already proven genuinely
    complex, via `reform_count`), record the decomposed part_of/marker
    component predications back onto the SentenceParse, mark reform_done, and
    bump the flow's own reform_count (the max_order derivation's own residual-
    mass signal for the REST of this flow).

    Called from TWO places: (a) inline at the end of `_shim_monitoring`'s own
    pass (the opportunistic same-tick catch, when timing allows); (b) the
    ALWAYS-ON `reform_reflex` (seeds/reading_reform_reflex.json), registered
    below as `reform_advance` — the guaranteed catch-all, because empirically
    (verified live, tick-by-tick) the 'monitoring' AnalysisStage's own ONE-SHOT
    material-triggered dispatch can settle to 'done' in an EARLIER tick than
    reform_overcomplex_clause's rule-fixpoint pass makes reform_pending
    visible, so relying on (a) alone silently drops the reform. Both call
    sites are idempotent (the reform_pending/reform_done guard), so running
    from both is harmless — it is the SAME mechanical action, never a second
    decision."""
    from domains import reading_collapse as rc
    from domains import reading_norms as rn
    flow = getattr(ad, "flow", None)
    fnode = getattr(ad, "_flow_node", None)
    register = rn.flow_register(ad.s, flow)
    for n in ad.s.nodes("SentenceParse"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        if at.get("reform_pending") != 1 or at.get("reform_done") == 1:
            continue
        reform_count = 0.0
        if fnode is not None:
            reform_count = float(ad.s.node(fnode)["attrs"].get("reform_count", 0.0) or 0.0)
        max_order = rn.effective_max_order(ad, register, reform_count=reform_count)
        dec = rc.read_clause_order_n(ad, at.get("sentence"), max_order=max_order, write=False)
        ad.s.set_attr(n, "reform_predications", json.dumps(dec.get("order_n_predications") or []))
        ad.s.set_attr(n, "reform_members", json.dumps(dec.get("members") or []))
        ad.s.set_attr(n, "reform_depth", float(dec.get("depth") or 1))
        ad.s.set_attr(n, "reform_done", 1.0)
        rn.record_reform(ad.s, fnode)


def _execute_pending_reform_ingests(ad) -> None:
    """BLIND-SPOT CLOSURE R8 (2026-07-12) — the mechanical executor for the
    `ingest_reform_components` RULE's decision (seeds/reading_reform_ingest.json):
    a completed reform (`reform_done=1`) whose components a RULE already
    decided belong in the situation model (`reform_ingest_pending=1`) gets
    those components MINTED as real SmEntity/part_of graph structure —
    `_enact_advance`-precedent, evaluate-and-apply-only, never a decision.

    A `part_of` reform predication (the enumeration-list descent —
    `read_clause_order_n`'s `part_of(member, head)`) is not a change-of-state
    verb `situation_model_reader.ingest_predication` would mint, so it is
    minted via the EXISTING `inference_generation._mint_part_of` mechanical
    idiom instead (reused verbatim, the SAME "not a decision, a direct
    admissibility-gated edge write" idiom that function's own docstring
    documents) — the part SmEntity is additionally stamped `from_reform=1`
    for provenance (so a renderer or a later query can tell a reform-derived
    component from a directly-observed one). Any OTHER reform predication (a
    compound-tail marker) is handed to `situation_model_reader.
    ingest_predication` (reused as-is) — deliberately NOT
    `coref_entities.resolve_and_ingest`: the reformed sentence's order-1
    predications already went through the live spine's coref bookkeeping
    ONCE (`_touch_entity` mention counts, Cf/Cb centering), so re-running
    that bookkeeping over the SAME sentence's decomposed components would
    double-count salience and distort every downstream salience Argmax
    (measured: it flipped 'The Travelling Musicians' protagonist derivation
    from 'dog' to 'robbers'). The re-ingest is about the STRUCTURE the
    reform recovered, never a second count of the same mentions.

    Guarded by `reform_ingested` (`kin_monitored`/`reform_done`'s own
    exactly-once idiom, one stage up) — re-running this executor on an
    already-ingested SentenceParse is a no-op. Called from TWO places, same
    rationale as `_execute_pending_reforms`'s own docstring: (a)
    opportunistically inline at the end of `_shim_monitoring`'s pass; (b) the
    ALWAYS-ON `reform_ingest_reflex` (seeds/reading_reform_ingest.json),
    registered below as `reform_ingest_advance` — the guaranteed catch-all,
    because the rule that sets `reform_ingest_pending` cannot fire until
    AFTER `reform_done` is written by (a)'s own earlier call in this SAME
    function's sibling, so the FIRST opportunistic call here can never catch
    its own just-completed reform; only a LATER pass (this monitoring stage
    re-arming on SmEntity growth, or the reflex) ever does.

    THE ONCE-PER-SENTENCE KINSHIP GUARD IS UNTOUCHED: `_shim_monitoring`'s
    own `kin_monitored` loop reads a SentenceParse's `resolved_predications`
    attr ONLY — never `reform_predications` — so re-ingesting a reform's
    components here can never re-trigger or duplicate a kinship scan (the
    guard this closure was deliberately deferred against, per the reform
    executor's own docstring, when read closely turns out to be a NON-ISSUE
    once the two attrs are kept separate, which they always have been)."""
    import json as _json
    from domains import inference_generation as ig
    from domains import situation_model_reader as smr
    flow = getattr(ad, "flow", None)
    for n in ad.s.nodes("SentenceParse"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        if at.get("reform_ingest_pending") != 1 or at.get("reform_ingested") == 1:
            continue
        # the UNIT for minting is THIS row's own flow stamp (the row always
        # carries it when its flow does) — never only `ad.flow`, because the
        # ALWAYS-ON reflex can fire this executor from the live persistent
        # adapter (ad.flow unset) on a row a `_LAAdapter` flow minted, and
        # the components must land in THAT flow's unit-scoped entity pool,
        # not the global one.
        unit = at.get("flow") if at.get("flow") is not None else flow
        try:
            preds = _json.loads(at.get("reform_predications") or "[]")
        except Exception:
            preds = []
        turn = 0
        for p in preds:
            if not p or len(p) < 3:
                continue
            rel = str(p[0])
            if rel == "part_of":
                ig._mint_part_of(ad, str(p[1]), str(p[2]), unit=unit)
                ent = smr._entity(ad, str(p[1]), unit=unit)
                ad.s.set_attr(ent, "from_reform", 1.0)
            else:
                turn += 1
                smr.ingest_predication(ad, list(p), t=turn, unit=unit)
        ad.s.set_attr(n, "reform_ingested", 1.0)


def _shim_tom(ad) -> None:
    from domains import character_tom as ctom
    bb = _bb(ad)
    ctom.ensure_seeds(ad)
    flow = getattr(ad, "flow", None)
    tom_results = []
    for i, s in enumerate(_sentences_from_graph(ad), start=1):   # INPUT
        rec = ctom.ingest_attitude_sentence(ad, s, t=i, unit=flow)
        tom_results.append({"sentence": s, "result": rec})
    bb["tom_results"] = tom_results


def _shim_narrative(ad) -> None:
    from domains import narrative_structure as ns
    bb = _bb(ad)
    # NARRATIVE STRUCTURE: the story-grammar arc over the comprehension graph
    # (goal + enabling chain + discourse pairs), ALL re-read from graph nodes.
    # `unit=ad.flow` (Wave 1A) stamps every minted NarrativeRole with this flow's
    # own identity.
    bb["narrative_arc"] = ns.recognize_narrative_structure(ad, {
        "goal": _goal_from_graph(ad),
        "enabling_chain": _enabling_chain_from_graph(ad),
        "discourse": {"pairs": _discourse_pairs_from_graph(ad)}},
        unit=getattr(ad, "flow", None))


def _shim_trope(ad) -> None:
    from domains import trope_theme as tt
    bb = _bb(ad)
    # TROPE + THEME: one level up from the arc, ShapeDecode set-cover over the
    # arc's own roles (graph) + the causal record (CausalLink) + the blocked_gap/
    # coref_number node markers trope_theme now reads directly. `unit=ad.flow`
    # (Wave 1A) stamps every minted Trope/Theme with this flow's own identity.
    view = {"narrative_arc": _narrative_arc_from_graph(ad),
            "causal": _causal_from_graph(ad)}
    bb["trope_theme"] = tt.recognize_tropes_and_theme(ad, view, unit=getattr(ad, "flow", None))


# --- production stages (literary_analysis, reused) ------------------------- #
def _produce_contexts(ad):
    """Re-derive the per-entity produce contexts (frames + rendered clauses)
    ENTIRELY from the graph — the graph-native replacement for the old
    `bb['_produce_ctx']` inter-stage cache. Each section stage calls this, so no
    Python state passes between the produce stages; the LanguageProduction
    render is deterministic, so re-deriving per stage is byte-identical."""
    from domains import narrative_structure as ns
    from domains import literary_analysis as la
    graph = _comprehension_view_from_graph(ad)
    sentences = graph.get("sentences") or []
    preds = la._sentence_predications(graph)
    tt_results = (graph.get("trope_theme") or {}).get("results") or []
    arcs = (graph.get("narrative_arc") or {}).get("arcs") or []
    ctxs = []
    for entity in [a.get("entity") for a in arcs]:
        roles = ns.read_narrative_roles(ad, entity, unit=getattr(ad, "flow", None))
        roles_by = la._role_map([r for r in roles if r.get("role")])
        if not roles_by:
            continue
        frames = la._frames_for(ad, graph, entity, roles_by, preds, sentences)
        producer = la._build_producer(list(frames.values())) if frames else None
        produced = {}
        if producer is not None:
            for key, fr in frames.items():
                produced[key] = la._produce(producer, fr)
        tres = next((r for r in tt_results if r.get("entity") == entity), {})
        ctxs.append({"entity": entity, "roles_by": roles_by, "preds": preds,
                     "frames": frames, "produced": produced,
                     "tropes": tres.get("tropes") or [], "theme": tres.get("theme")})
    return graph, ctxs


def _shim_meaning_inference(ad) -> None:
    """MEANING-INFERENCE STAGE (2026-07-12, seeds/meaning_inference_stage.json):
    mechanical re-read of THIS flow's own SentenceParse nodes through
    `reading_collapse.read_clause(agent, sentence, write=True)` -- the exact
    call that already fires all five meaning-inference sources (selectional/
    definition/morphology/analogy/in-situ construction) and their seeded
    infer_sense_* rules (seeds/meaning_inference.json) when called directly.
    `read_and_comprehend`'s own ~24 read_clause calls per sentence pair are
    ALWAYS write=False (its own decomposition machinery), so the annotators
    (which read existing Concept nodes) never fire without this stage.

    Purely additive graph data (Concept/Predication/PredicationSlot/
    InferredSense/AffixCandidate/ConceptSignature) -- no SmEntity/SmEvent/
    DiscourseEvent/NarrativeRole/Trope/Claim node is ever written here, so
    this cannot perturb any earlier stage's already-computed output (the
    comprehension report is byte-identical with/without this stage). The
    seed's own dispatch rule (la_dispatch_meaning_inference) gates this on
    'monitoring' having reached 'done' -- the last comprehension stage
    GUARANTEED to complete -- so it always runs LAST.

    NO DECISION HERE: the source/mint/combine/abstain/supersede logic all
    lives in seeds/meaning_inference.json's rules (loaded automatically,
    idempotently, by the annotators read_clause(write=True) already calls);
    this shim only re-invokes the SAME read_clause() call the direct-call
    path already uses, per SentenceParse, guarded idempotent (`mi_reread`)
    so a stage advance is never repeated for the same sentence.

    CLAUSE GRAIN (2026-07-12): a real article sentence is multi-clause and
    RUN-ON; a single whole-sentence read_clause() mangles it, so the passive/
    unsaid/actor annotators (which also fire on the SAME write=True call --
    ma.annotate_passive_predication @reading_collapse:1566,
    ma.annotate_relational_noun @1461, ag.annotate_actor_action @1578) only
    ever see the first clause. The parser's clause recognition is now FIRST-
    CLASS GRAPH DATA: `_mint_sentence_parse_nodes` persists one `ClauseParse`
    node per recognised clause (`sp -has_clause-> cp`) at ingest, the clause
    twin of Mention tokenization. This shim iterates those graph nodes -- the
    SAME mechanical shape as its SentenceParse loop, NO Python conditional
    over graph state -- and re-reads each clause with write=True. It also
    keeps the whole-sentence read (cross-clause constructions: an appositive/
    definition genus that spans a comma, "A florx, a small bird, sang.").
    Every read is strictly ADDITIVE and idempotent by the annotators' own
    keys (a passive the whole read caught is not re-minted; the clauses it
    mangled past now mint their own). Every mint/deletion/framing/goal
    DECISION stays in the seeded rules the annotators load."""
    from domains import reading_collapse as rc
    flow = getattr(ad, "flow", None)
    for n in ad.s.nodes("SentenceParse"):
        at = ad.s.node(n)["attrs"]
        if flow is not None and at.get("flow") != flow:
            continue
        if at.get("mi_reread") == 1:
            continue
        sentence = at.get("sentence")
        # Each recognised clause FIRST, persisted as graph data at ingest -- a
        # mechanical iteration over graph nodes (like the SentenceParse loop),
        # so a run-on's later clauses each mint their own analysis. The clause's
        # LATTICE-DECODED WORD-LIST feeds read_clause's word-list path directly
        # (no re-tokenization of a re-joined string -- tokenization stays
        # graph-native and happens exactly once, at ingest).
        #
        # ORDER MATTERS (2026-07-12): a single clean clause reads MORE PRECISELY
        # than the whole run-on -- e.g. it captures the by-phrase agent of "the
        # findings were suppressed by the committee" (agent_filled), which the
        # whole-sentence read mangles into an agent-BLIND passive because the
        # by-phrase is buried in the blob. Reading clauses first lets the
        # precise per-clause fact win the annotators' own (verb,patient)
        # idempotency; the whole read that follows only fills what NO clause
        # covered (cross-clause constructions: an appositive/definition genus
        # spanning a comma), its degraded per-clause duplicates idempotency-
        # blocked. No new decision -- the existing idempotency guard + this
        # ordering.
        for cp in ad.s.neighbours(n, "has_clause"):
            raw = ad.s.node(cp)["attrs"].get("clause_words")
            if not raw:
                continue
            words = json.loads(raw)
            if words:
                rc.read_clause(ad, words, write=True)
        if sentence:
            # Whole-sentence read (cross-clause constructions), unchanged.
            rc.read_clause(ad, sentence, write=True)
        # GOAL LAYER (auto-fire): the conflicting-goals disclaimer analysis. A
        # disclaimer cue ('not racist but') spans the clause boundary -- and the
        # contrast-coordinator split separates 'not racist' from 'but ...' -- so
        # it is read at SENTENCE grain, not per clause. The default DisclaimerCue
        # codebook + the method text self-load (DATA), and the classify-by-join
        # rule is AGENT-AUTHORED once from that held method (never seeded). All
        # mechanical here: emit candidates, self-load data, run the authoring
        # faculty; every classification DECISION is the agent-authored rule's
        # Eq-join against the taught codebook.
        if sentence:
            from domains import actor_goals as ag
            # (a) conflicting-goals disclaimer -- sentence-grain phrase cue.
            ag.ensure_conflicting_goals_defaults(ad)
            ag.annotate_disclaimer_candidates(ad, sentence)
            ag.ensure_conflicting_goals_rule(ad)
            # (b) surface-inversion -- sentence-grain phrase cue (a distancing
            # phrase like 'the disgusting notion that' marks the surface content
            # as not the speaker's own stance). (c) temporal-conflict + (d)
            # named-trope -- DOCUMENT-level: annotate_action_pairs joins the
            # ActorAction facts the clause reads already minted (same actor +
            # object, opposing verbs) into an ActionPairFact, the temporal rule
            # classifies the support-then-undermine pair, and the trope rule
            # names it (Trojan Horse, ...). All idempotent, so re-running per
            # sentence converges to the correct document-level state; every
            # classification DECISION is an agent-authored rule's Eq-join.
            ag.ensure_goal_layers_defaults(ad)
            ag.annotate_utterance_phrases(ad, sentence)
            ag.ensure_surface_inversion_rule(ad)
            ag.annotate_action_pairs(ad)
            ag.ensure_temporal_conflict_rule(ad)
            ag.ensure_named_trope_rule(ad)
            # (e) epistemic gap -- the deepest layer (deception vs introspection-
            # gap). The reads' beliefs (temporal conflict, action pairs, actor
            # goals) auto-produce the structural EVIDENCE via the signal
            # detectors + the agent-authored classify-by-join. The VERDICT is the
            # context-dependent assess_epistemic_lean COMBINE, run deliberately
            # AFTER the world supplies the actor's class/type (annotate_actor_
            # class) -- "a better model of the actor's environment than the
            # actor's self-model" -- NOT in this stage, so the interval reflects
            # the available context. See domains/actor_goals.assess_epistemic_lean.
            ag.ensure_epistemic_defaults(ad)
            ag.run_epistemic_signal_detectors(ad)
            ag.ensure_epistemic_evidence_rule(ad)
        ad.s.set_attr(n, "mi_reread", 1.0)


def _shim_produce_frames(ad) -> None:
    # No inter-stage cache: the four section stages each re-derive their own
    # produce contexts from the graph. This stage holds no state — it remains
    # the dispatch GATE the section stages depend on in the seed.
    return


def _shim_produce_summary(ad) -> None:
    from domains import literary_analysis as la
    graph, ctxs = _produce_contexts(ad)
    for ctx in ctxs:
        _record_claims(ad, la._build_summary(
            ad, graph, ctx["entity"], ctx["roles_by"],
            ctx["preds"], ctx["produced"], ctx["frames"]))


def _shim_produce_structure(ad) -> None:
    from domains import literary_analysis as la
    graph, ctxs = _produce_contexts(ad)
    for ctx in ctxs:
        _record_claims(ad, la._build_structure(
            ad, graph, ctx["entity"], ctx["roles_by"],
            ctx["preds"], ctx["produced"], ctx["frames"]))


def _shim_produce_technique(ad) -> None:
    from domains import literary_analysis as la
    graph, ctxs = _produce_contexts(ad)
    for ctx in ctxs:
        _record_claims(ad, la._build_technique(ad, graph, ctx["entity"], ctx["tropes"]))


def _shim_produce_theme(ad) -> None:
    from domains import literary_analysis as la
    graph, ctxs = _produce_contexts(ad)
    for ctx in ctxs:
        _record_claims(ad, la._build_theme(
            ad, graph, ctx["entity"], ctx["theme"], ctx["tropes"]))


_STAGE_SHIMS = {
    "spine": _shim_spine,
    "infer_goal": _shim_infer_goal,
    "discourse": _shim_discourse,
    "infer_causal": _shim_infer_causal,
    "enabling": _shim_enabling,
    "centrality": _shim_centrality,
    "monitoring": _shim_monitoring,
    "tom": _shim_tom,
    "narrative": _shim_narrative,
    "trope": _shim_trope,
    "meaning_inference": _shim_meaning_inference,
    "produce_frames": _shim_produce_frames,
    "produce_summary": _shim_produce_summary,
    "produce_structure": _shim_produce_structure,
    "produce_technique": _shim_produce_technique,
    "produce_theme": _shim_produce_theme,
}

# the comprehension stages (mint for every reading goal) and the production
# stages (mint only for a produce-analysis goal). 'meaning_inference' runs
# LAST (see seeds/meaning_inference_stage.json's la_dispatch_meaning_inference
# -- gated on 'monitoring' done) -- list position here is cosmetic (dispatch
# is graph-precondition-driven, not list-order-driven), kept last for clarity.
_COMPREHENSION_STAGES = ["spine", "infer_goal", "discourse", "infer_causal",
                         "enabling", "centrality", "monitoring", "tom",
                         "narrative", "trope", "meaning_inference"]
_PRODUCE_STAGES = ["produce_frames", "produce_summary", "produce_structure",
                   "produce_technique", "produce_theme"]

# --------------------------------------------------------------------------- #
#  THE FIVE CORTICES — the reading as a SOCIETY OF CORTICES (seeds/
#  reading_cortices.json), not a linear dispatch chain. Each faculty STAGE is a
#  member of one cortex; the cortex's per-tick Reflex advances whichever of its
#  stages the la_dispatch_* rules have dispatched (i.e. whose data-preconditions
#  now hold). All five reflexes fire EVERY cognitive_tick; the reading emerges
#  from their mutual constraint over ticks (LANGUAGE feeds SITUATION feeds
#  NARRATIVE, ... — the order is the DATA-dependency, not a hardcoded chain).
#  The membership below is static configuration (like _STAGE_SHIMS), mirrored as
#  graph data on the Cortex nodes (`stages` attr) so it is graph-inspectable.
# --------------------------------------------------------------------------- #
_CORTEX_OF = {
    "spine": "language",
    "infer_goal": "situation", "discourse": "situation", "infer_causal": "situation",
    "enabling": "situation", "centrality": "situation",
    "tom": "social",
    "narrative": "narrative", "trope": "narrative",
    "monitoring": "executive", "produce_frames": "executive",
    "produce_summary": "executive", "produce_structure": "executive",
    "produce_technique": "executive", "produce_theme": "executive",
    "meaning_inference": "executive",
}
_CORTEX_NAMES = ["language", "situation", "social", "narrative", "executive"]

# THE ORDER-N COLLAPSES ARE ASYNC + REVISABLE (2026-07-07). The FIRST-PASS stages
# (spine + the situation-model build) stay ORDERED, one-shot: they have no la_rearm
# rule, so absent an external re-feed each fires exactly once when its data-
# precondition holds. The HIGHER-ORDER recognitions (the narrative arc, trope/theme,
# executive monitoring) are made material-triggered + REVISABLE: la_rearm_* rules in
# seeds/literary_analysis_driving.json re-arm them (done -> pending) when their INPUT-
# node set GROWS or a coherence break flags a GlobalIncoherence -- the exact
# sd_redecode/codebook_epoch re-arm-on-growth mechanism, mirrored for the reading. The
# trigger node type per order-N stage is the material it collapses over ("events ->
# arc; arc -> trope; the situation model -> monitoring"). The advance shim stamps
# input_epoch/coh_epoch at collapse time (mechanical count I/O -- the grow_part_library
# epoch-bump precedent); the RE-ARM DECISION is the graph rule, fired by cognitive_tick.
# A stage NOT in this map keeps the one-shot `done` latch (ordered first pass).
_ORDER_N_TRIGGER = {"narrative": "SmEvent", "trope": "NarrativeRole",
                    "monitoring": "SmEntity"}

# On a coherence-break-triggered re-collapse (a NEW GlobalIncoherence since the
# stage's last collapse), the order-N stage SUPERSEDES its prior verdict so the
# re-collapse can genuinely CHANGE the interpretation (not merely re-run additively).
# The nodes each order-N stage owns and clears on supersession (remove_node cascades
# dangling edges -- verified). Growth re-collapses do NOT supersede (they are additive;
# the report reads only canonical setup/problem/solution/resolution roles, so additive
# growth stays byte-identical).
_ORDER_N_OWNS = {"narrative": ["NarrativeRole"],
                 "trope": ["Trope", "Theme", "TropeEvidence"]}


def _supersede_order_n(ad, stage_name: str) -> None:
    """Clear an order-N stage's prior output nodes (mechanical graph I/O) so a
    re-collapse recomputes cleanly -- the hold-open / re-read insight: the collapse
    re-collapses on new material or a non-sequitur, superseding rather than accreting.

    LEARNED-QUANTUM SUPERSESSION (2026-07-07): the trope stage's sd-loop learning can
    mint a LEARNED ShapeSignatureTrope quantum from a TRANSIENTLY-PARTIAL arc (e.g.
    an incrementally-streamed story whose arc is momentarily setup+problem only, no
    seeded trope yet covering it). That learned quantum must NOT persist into the
    codebook and corrupt a LATER full-arc decode (the set-cover would prefer the
    narrow learned quantum over the wider seeded trope). So on a trope re-collapse we
    also drop the LEARNED quanta (learned==1) -- never the seeded codebook nodes --
    so the re-collapse re-decodes against the seeded codebook and re-learns only if
    the CURRENT arc is still genuinely uncovered.

    FLOW-SCOPED (Wave 1A): every clear below is confined to `ad.flow`'s own
    nodes (`unit`/`flow` attr match) — a re-collapse on THIS flow must never
    wipe another flow's already-completed NarrativeRole/Trope/Theme/Claim
    nodes or re-arm another flow's already-returned produce stages. `ad.flow`
    unset is the byte-identical legacy (whole-graph) clear."""
    flow = getattr(ad, "flow", None)
    for t in _ORDER_N_OWNS.get(stage_name, []):
        for n in list(ad.s.nodes(t)):
            if flow is not None and ad.s.node(n)["attrs"].get("unit") != flow:
                continue
            ad.inner.remove_node(n)
    if stage_name == "trope":
        for n in list(ad.s.nodes("ShapeSignatureTrope")):
            at = ad.s.node(n)["attrs"]
            if at.get("learned") != 1:
                continue
            if flow is not None and at.get("unit") != flow:
                continue
            ad.inner.remove_node(n)
        # the PRODUCE section reads the trope/theme; a superseded trope verdict
        # means its already-minted report Claims are stale (an incrementally-
        # streamed arc can fire produce early off a transient trope). Clear the
        # Claims and RE-ARM the one-shot produce stages so the report re-derives
        # from the FINAL trope -- the same supersede-not-accrete discipline the
        # order-N stages themselves follow. In the non-streaming (flat) path the
        # trope collapses once over the whole arc, so this never fires there.
        for n in list(ad.s.nodes("Claim")):
            if flow is not None and ad.s.node(n)["attrs"].get("flow") != flow:
                continue
            ad.inner.remove_node(n)
        bb = ad._master.get("analysis_bb")
        if isinstance(bb, dict):
            bb["claims"] = []
            bb["sections"] = {}
        for st in ad.s.nodes("AnalysisStage"):
            at = ad.s.node(st)["attrs"]
            if at.get("name") not in _PRODUCE_STAGES or at.get("status") != "done":
                continue
            if flow is not None and at.get("flow") != flow:
                continue
            ad.s.set_attr(st, "status", "pending")


def _cortex_node(ad, name):
    for n in ad.s.nodes("Cortex"):
        if ad.s.node(n)["attrs"].get("name") == name:
            return n
    return None


def _advance_one_stage(ad, st, at) -> None:
    """Advance ONE already-dispatched stage node (the shared body both
    `_advance_cortex_stage` and `_advance_dispatched_stage` call — Wave 1A
    de-duplication): look up its named shim, supersede-if-re-collapse, run it,
    mark done, stamp the order-N epoch counters. Extracted so BOTH advance
    paths stay order-N-safe — before this, `_advance_dispatched_stage` was a
    NAIVE advancer with no supersede/epoch logic, so registering the orphaned
    `analysis_advance` reflex onto it raced the cortex reflexes' own
    order-N-aware advance and could double-mint an order-N stage's output
    (reproduced: it double-minted a Trope, the second `_mint_trope` hitting the
    'already held' short-return branch). One shared body removes the race
    class entirely — whichever reflex gets there first does the SAME correct
    thing."""
    name = at.get("name")
    shim = _STAGE_SHIMS.get(name)
    if shim is None:
        return                             # no shim for this stage name — honest no-op
    trig = _ORDER_N_TRIGGER.get(name)
    if trig is not None and int(at.get("advance_count") or 0) > 0:
        # RE-COLLAPSE (not the first collapse — the la_rearm_* rule brought this
        # order-N stage back to pending because its material GREW or a coherence
        # break flagged a GlobalIncoherence): SUPERSEDE the prior verdict so the
        # collapse recomputes cleanly over the CURRENT material and the arc/theme
        # genuinely CHANGE (the hold-open / re-read insight — an order-N collapse
        # re-collapses on new material or a non-sequitur, superseding rather than
        # accreting). Byte-identical with the one-shot baseline is preserved: the
        # final recompute over the full material is deterministic and the report
        # reads only the canonical setup/problem/solution/resolution roles.
        _supersede_order_n(ad, name)
    shim(ad)
    ad.s.set_attr(st, "status", "done")
    # per-stage advance counter (how many times this stage collapsed) — a first-
    # pass stage settles at 1; an order-N stage climbs as it re-collapses.
    ad.s.set_attr(st, "advance_count", int(at.get("advance_count") or 0) + 1)
    if trig is not None:
        # STAMP the epochs the la_rearm_* rules compare against (mechanical count
        # I/O — the grow_part_library epoch-bump precedent). input_epoch = how much
        # material this collapse saw; coh_epoch = how many coherence breaks it saw.
        ad.s.set_attr(st, "input_epoch", len(ad.s.nodes(trig)))
        ad.s.set_attr(st, "coh_epoch", len(ad.s.nodes("GlobalIncoherence")))


def _advance_cortex_stage(ad, cortex: str) -> None:
    """The per-cortex reflex RESPONSE (the I/O boundary, shaped exactly like
    _advance_dispatched_stage / _question_pursue_advance): advance ONE dispatched
    stage BELONGING TO THIS CORTEX via its named shim, mark it done. NO branch on
    graph state to pick a faculty — a lookup of which shim the stage names,
    filtered to this cortex's own stages. All five cortices run this (each with
    its own name) every tick; each processes only whatever of its inputs are
    ready, so they advance concurrently as the data-dependencies unlock.

    FLOW-SCOPED (Wave 1A): also filtered to THIS adapter's own flow (`at.get
    ("flow") == ad.flow`, the same membership-filter idiom as the pre-existing
    `cortex` filter above it) — a defence-in-depth backstop alongside the
    flow-scoped `la_rearm_*` seed rules: even if a rearm rule's Count ever
    mis-fires and flips an EARLIER, already-returned flow's order-N stage back
    to `pending`/`dispatched`, this adapter (bound to the CURRENT flow) never
    advances it, so it can never supersede/re-render a different flow's
    already-delivered report. `ad.flow` unset is the byte-identical legacy
    (whole-graph) behaviour."""
    flow = getattr(ad, "flow", None)
    for st in ad.s.nodes("AnalysisStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("status") != "dispatched" or at.get("cortex") != cortex:
            continue
        if flow is not None and at.get("flow") != flow:
            continue
        if _STAGE_SHIMS.get(at.get("name")) is None:
            continue                       # no shim for this stage name — honest no-op
        _advance_one_stage(ad, st, at)
        return                             # one stage advanced per firing


def _register_cortices(ad) -> None:
    """Install the five graph-resident Cortex bundles + reflexes (idempotent) and
    register each cortex's thin advance response. The Reflex nodes ship as seed
    data (the `reflexes` manifest key); fire_reflexes discovers + fires them.

    Also (re-)registers the OLDER, single `analysis_advance` reflex's response
    (literary_analysis_driving.json's own `reflexes` entry, pre-dating the
    5-cortex split) — it is still graph-resident (kept for
    `test_sequencing_lives_in_seed_rules_and_a_reflex`'s source audit) but had
    NO Python response registered anywhere post-cortex-split, so it was a
    second standing phantom (Wave 1A): its stimulus (any AnalysisStage
    dispatched, at all) trips on every normal dispatch, `fire_reflexes` stamps
    `fire_count`/`last_fired_tick` regardless of whether a response resolves,
    and `_master["reflex_responses"]` had no entry for it. It is harmlessly
    redundant with the cortices (same `_advance_dispatched_stage` /
    `_advance_cortex_stage` shape, one stage per firing) — registering it
    simply makes it a REAL advance instead of a no-op count.

    ALSO registers `reform_advance` (Wave: dynamic-thresholds/reform,
    2026-07-11, seeds/reading_reform_reflex.json's `reform_reflex`) — the
    ALWAYS-ON executor for `_execute_pending_reforms` (see that function's own
    docstring for why a dedicated reflex is needed alongside its opportunistic
    same-pass call inside `_shim_monitoring`).

    ALSO registers `reform_ingest_advance` (blind-spot closure R8, 2026-07-12,
    seeds/reading_reform_ingest.json's `reform_ingest_reflex`) — the
    ALWAYS-ON executor for `_execute_pending_reform_ingests`, same rationale
    one stage further down the reform pipeline."""
    _ensure_seed_chain(ad.s, ad.inner, ad.agent,
                       ("reading_cortices", "reading_reform_reflex", "reading_reform_ingest"))
    for name in _CORTEX_NAMES:
        ad.register_reflex_response(
            "%s_cortex_advance" % name,
            (lambda nm: lambda a: _advance_cortex_stage(a, nm))(name))
    ad.register_reflex_response("analysis_advance", lambda a: _advance_dispatched_stage(a))
    ad.register_reflex_response("reform_advance", lambda a: _execute_pending_reforms(a))
    ad.register_reflex_response("reform_ingest_advance",
                                lambda a: _execute_pending_reform_ingests(a))


def _place_in_cortex(ad, stage_node, cortex: str) -> None:
    """Mechanical membership I/O: stamp the stage's `cortex` attr (the reflex
    stimulus filter) and wire its in_cortex edge to the Cortex node."""
    ad.s.set_attr(stage_node, "cortex", cortex)
    cx = _cortex_node(ad, cortex)
    if cx is not None:
        ad.inner.add_edge_unchecked(stage_node, "in_cortex", cx)


# --------------------------------------------------------------------------- #
#  Claim minting + blackboard read-off (mechanical I/O).
# --------------------------------------------------------------------------- #
def _record_claims(ad, claims) -> None:
    flow = getattr(ad, "flow", None)
    bb = _bb(ad)
    for c in (claims or []):
        order = len(bb["claims"])
        bb["claims"].append(c)
        bb["sections"].setdefault(c["section"], []).append(c["sentence"])
        attrs = {"section": c["section"], "sentence": c["sentence"],
                 "kind": c["kind"], "order": float(order)}
        if flow is not None:
            attrs["flow"] = flow             # FLOW-SCOPED (Wave 1A) — see _supersede_order_n
        cn = ad.s.add_node("Claim", attrs)
        ad.inner.add_edge_unchecked(ad.agent, "has_claim", cn)


def _comprehension_view(bb: dict) -> dict:
    """The accumulated comprehension result dict (the SAME keys the old
    read_and_comprehend returned) — a mechanical projection of the blackboard,
    with honest empty defaults for any stage that has not (yet) run."""
    return {
        "text": bb.get("text"),
        "sentences": bb.get("sentences") or [],
        "spine": bb.get("spine") or {},
        "goal_gaps": bb.get("goal_gaps") or [],
        "goal": bb.get("goal") or [],
        "precondition_gaps": bb.get("precondition_gaps") or [],
        "blocking": bb.get("blocking") or [],
        "bridging_gaps": bb.get("bridging_gaps") or [],
        "bridging": bb.get("bridging") or [],
        "elaborative_candidates": bb.get("elaborative_candidates") or [],
        "discourse": bb.get("discourse") or {},
        "centrality": bb.get("centrality") or {},
        "causal_gaps": bb.get("causal_gaps") or [],
        "causal": bb.get("causal") or [],
        "enabling_chain": bb.get("enabling_chain") or [],
        "monitoring": bb.get("monitoring") or [],
        "tom_results": bb.get("tom_results") or [],
        # canonical empty shapes when a data-dependency trigger never fires
        # (a non-narrative source has no SmEvent arc / no NarrativeRole trope):
        # exactly what recognize_narrative_structure / recognize_tropes_and_theme
        # return for an empty input — the honest null, supplied at read-off.
        "narrative_arc": bb.get("narrative_arc") or {"arcs": []},
        "trope_theme": bb.get("trope_theme") or {"results": []},
    }


# --------------------------------------------------------------------------- #
#  THE REFLEX RESPONSE — the I/O boundary (the _question_pursue_advance shape):
#  advance ONE dispatched stage via its named shim, mark it done. NO branch on
#  graph state to pick a faculty — a lookup of which shim the stage names.
# --------------------------------------------------------------------------- #
def _advance_dispatched_stage(ad) -> None:
    """FLOW-SCOPED (Wave 1A) + ORDER-N-SAFE: shares `_advance_one_stage` with
    the cortex reflexes' own advance (see that function's docstring for why —
    this used to be a naive advancer with no supersede/epoch logic, which
    double-minted an order-N stage's output when both this AND a cortex
    reflex could reach the same dispatched stage)."""
    flow = getattr(ad, "flow", None)
    for st in ad.s.nodes("AnalysisStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("status") != "dispatched":
            continue
        if flow is not None and at.get("flow") != flow:   # FLOW-SCOPED (Wave 1A)
            continue
        if _STAGE_SHIMS.get(at.get("name")) is None:
            continue                       # no shim for this stage name — honest no-op
        _advance_one_stage(ad, st, at)
        return                             # one stage advanced per firing


# --------------------------------------------------------------------------- #
#  INGEST + GOAL + STAGES (mechanical mint) and the PUMP.
# --------------------------------------------------------------------------- #
def _ingest_source(ad, text: str):
    src = ad.s.add_node("Source", {"text": text})
    return src


def _mint_goal(ad, source, *, produce: bool, register: Optional[str] = None):
    """`register` (Wave: foveation-as-hint, task 3): the register that HINTED
    this flow's aperture — stamped onto the Goal so the seeded
    `escalate_*` rules (seeds/reading_aperture.json) can look up THIS flow's
    own `ApertureBudget{register}` belief. `None` (every pre-wave caller,
    e.g. `run_produce_over_graph`) normalises to `'default'` — a held,
    revisable budget row, never a Python literal the rules read around."""
    attrs = {"kind": "produce_analysis" if produce else "comprehend",
             "reading_report": 1.0, "status": "open",
             "register": register or "default"}
    flow = getattr(ad, "flow", None)
    if flow is not None:
        attrs["flow"] = flow
    if produce:
        attrs["produce_report"] = 1.0
    goal = ad.s.add_node("Goal", attrs)
    if source is not None:
        ad.inner.add_edge_unchecked(goal, "reads_source", source)
    try:
        from domains import interlocutor_model as _im
        _im.wanted_by(ad, goal)
    except Exception:  # noqa: BLE001 -- provenance is best-effort, never load-bearing
        pass
    return goal


def _mint_stages(ad, *, produce: bool, stages=None):
    """Mint one `AnalysisStage` per stage name, bundled into its cortex. `stages`
    (Wave 2, the APERTURE) is an optional subset of `_COMPREHENSION_STAGES` —
    `None` (every pre-Wave-2 caller) mints all ten, byte-identical. A narrower
    subset (e.g. `["spine"]`, the conversational aperture) means the OTHER
    faculties' stage nodes never exist, so the la_dispatch_* rules never
    dispatch them and their shims (and ensure_seeds/ensure_codebook calls)
    never run — the execution plan is exactly what the winning register's
    `stages` graph attr said it should be."""
    flow = getattr(ad, "flow", None)
    names = list(stages) if stages else list(_COMPREHENSION_STAGES)
    names = names + (list(_PRODUCE_STAGES) if produce else [])
    for name in names:
        attrs = {"name": name, "status": "pending"}
        if flow is not None:
            attrs["flow"] = flow             # FLOW-SCOPED (Wave 1A) — see _advance_cortex_stage
        st = ad.s.add_node("AnalysisStage", attrs)
        ad.inner.add_edge_unchecked(ad.agent, "has_analysis_stage", st)
        _place_in_cortex(ad, st, _CORTEX_OF[name])       # bundle into its cortex


def _statuses(ad):
    return tuple(sorted((ad.s.node(n)["attrs"].get("name"),
                         ad.s.node(n)["attrs"].get("status"))
                        for n in ad.s.nodes("AnalysisStage")))


def _tick_reading(ad, max_ticks: int = 200) -> None:
    """DRIVE THE READING BY THE AGENT'S COGNITIVE TICK — tick to a steady state.

    This replaces the old hand-pump (`run_rules()` + `fire_reflexes()` reached
    into the engine). Each `ad.cognitive_tick()` IS one whole cognitive cycle:
    it settles the la_dispatch_* rule fixpoint (dispatch every stage whose graph
    DATA-precondition now holds) and fires the agent's reflexes — the FIVE
    CORTICES (seeds/reading_cortices.json). All five cortex reflexes are
    evaluated every tick; each advances one of ITS OWN dispatched stages, so the
    cortices process CONCURRENTLY — LANGUAGE mints the predications, then (next
    ticks) SITUATION builds the model off them, NARRATIVE forms the arc off that,
    EXECUTIVE monitors + produces — the reading EMERGING from their mutual
    constraint over ticks. The emergence ORDER is the DATA-dependencies (encoded
    in the la_dispatch preconditions), not a hardcoded Python stage chain, and
    NOT a hand-called run_rules/fire_reflexes anywhere in this loop. Stop when a
    tick changes no stage status (steady state)."""
    last = None
    for _ in range(max_ticks):
        ad.cognitive_tick()
        now = _statuses(ad)
        if now == last:
            break
        last = now


# --------------------------------------------------------------------------- #
#  THE DRIVER — the ONLY public entry. mint source + goal + stages, pump, read.
# --------------------------------------------------------------------------- #
def run_reading_flow(agent, text: str, *, report: str = "analysis",
                     window: int = 2, max_sentences: int = 40,
                     stages=None, register: Optional[str] = None) -> dict:
    """Seed the Jabberwock with a reading Goal + the source, run the comprehension
    ->analysis fixpoint, and return the accumulated blackboard (the comprehension
    views + `claims`/`sections` for a produce run). NO Python faculty sequence:
    ingest -> mint goal -> mint stages -> PUMP (rules+reflex) -> read-off.

    `stages` (Wave 2, the APERTURE as graph data): an optional subset of
    `_COMPREHENSION_STAGES` to mint, normally read off a register's own
    `stages` attr by the caller (`register_source._aperture_attrs` /
    `comprehension_reader.read_and_comprehend`). `None` mints all ten,
    byte-identical to every pre-Wave-2 call site.

    `stages`/`max_sentences`/`window` are a HINT, never fixed (2026-07-11,
    foveation-as-hint): they set the INITIAL aperture only. `register`
    (optional; defaults to `'default'` on the minted Goal) is threaded to
    `_mint_goal` so the seeded `escalate_*` rules (seeds/reading_aperture.json)
    can look up this flow's own `ApertureBudget` belief and — within that
    budget — mint ADDITIONAL AnalysisStage nodes for this SAME flow when the
    read's own output says the hint was too narrow (a truncated read, a
    heavy fallback-parse ratio, or a narrative shape under a light hint). No
    Python decides whether/how to widen; minting a new pending AnalysisStage
    for a flow IS the escalation — the existing `la_dispatch_*` machinery
    (unchanged) runs it, and `_tick_reading`'s SAME fixpoint below carries it
    to completion.

    PERSISTENT-SUBSTRATE SAFE (Wave 1A): `agent` may be a bare substrate OR a
    LIVE, long-lived `WorldAdapter` (the chat daemon's own adapter) that will
    keep ticking the SAME substrate long after this call returns. Everything
    minted this call is stamped with THIS call's own flow identity
    (`ad.flow` = the freshly-minted Source node id) and every re-reader below
    reads back ONLY that flow's own nodes — a second, third, ... call on the
    same substrate (a different text) never reads or mutates an earlier
    call's nodes (the stale-Source bug this replaces: every stage used to
    re-read "the first Source node ever minted", forever)."""
    s = getattr(agent, "s", agent)
    ad = _LAAdapter(s)
    _ensure_seed_chain(ad.s, ad.inner, ad.agent,
                       ("literary_analysis_driving", "reading_aperture",
                        "meaning_inference_stage"))
    _register_cortices(ad)                         # the five cortices + their reflexes
    if agent is not ad and hasattr(agent, "register_reflex_response"):
        # ALSO register on the caller's own LIVE adapter (Wave 1A, phantom-reflex
        # fix, option 1): `_master`/`reflex_responses` is per-Python-instance
        # state (substrate/world_adapter.py's `_master` property), never shared
        # across adapter objects over the same substrate — so a persistent
        # WorldAdapter that ticks this substrate AFTER this call returns would
        # otherwise discover the graph-resident Cortex Reflex nodes by name and
        # find NO registered response (a true phantom "fire": stimulus trips,
        # fire_count/last_fired_tick still get stamped, nothing runs). Combined
        # with the flow-scoped `la_rearm_*` rules (below) keeping the stimulus
        # itself false once idle, this makes a resolvable response available on
        # BOTH paths that could ever legitimately need it.
        _register_cortices(agent)
    ad._master["analysis_bb"] = {"text": text, "window": window,
                                 "max_sentences": max_sentences,
                                 "claims": [], "sections": {}}

    produce = (report == "analysis")
    source = _ingest_source(ad, text)              # 1. INGEST (text -> graph)
    ad._flow_node = source                          # the raw NodeID, for O(1) `.node()` lookups
    # THIS flow's identity (Wave 1A) — normalised to the PLAIN node value (`_vv`,
    # the SAME convention `story_tree.py`'s `unit` node ids already use, e.g.
    # `{"node": _v(root)}`), NOT the NodeID wrapper `add_node` returns: every
    # `unit=`-aware faculty call downstream (situation_model_reader._entity,
    # coref_entities.candidate_term, ...) embeds it as a native Term `Lit`
    # (JSON-serialised for the Rust evaluator) as well as a plain attr value —
    # a bare NodeID is not JSON-serialisable, so it must already be unwrapped
    # here, consistent with every existing `unit=` caller in the codebase.
    ad.flow = _vv(source)
    ad.s.set_attr(source, "flow", ad.flow)          # (Wave: foveation-as-hint) THIS
                                                    # flow's own Source carries its OWN
                                                    # identity as a plain attr — the SAME
                                                    # value every OTHER flow-scoped node
                                                    # (AnalysisStage/SentenceParse/Claim/
                                                    # now Goal) already stores as `flow` —
                                                    # so a seeded rule can match a Source
                                                    # against another flow-scoped node by
                                                    # a plain Eq, with no Python join.
    ad._master["analysis_bb"]["flow"] = ad.flow    # THIS flow's own identity (Wave 2:
                                                    # additive, for a caller that needs
                                                    # to re-find its own SentenceParse/
                                                    # SmEntity nodes by flow afterward,
                                                    # e.g. the chat shadow-read gateway).
    _mint_goal(ad, source, produce=produce, register=register)  # 2. GOAL (the only instruction)
    _mint_stages(ad, produce=produce, stages=stages)  # 3. STAGES (bundled into cortices)
    _tick_reading(ad)                              # 4. TICK to steady state (cortices) —
                                                    # this SAME fixpoint also runs any
                                                    # escalate_* rule (seeds/reading_
                                                    # aperture.json) and the AnalysisStage(s)
                                                    # it mints, so a caller never needs a
                                                    # second pump for an escalated read.
    return ad._master["analysis_bb"]               # 5. READ-OFF


def comprehension_result(agent, text: str, *, window: int = 2,
                         max_sentences: int = 40, stages=None,
                         register: Optional[str] = None) -> dict:
    """read_and_comprehend's return, goal-driven: the comprehension view."""
    bb = run_reading_flow(agent, text, report="comprehend", window=window,
                          max_sentences=max_sentences, stages=stages,
                          register=register)
    view = _comprehension_view(bb)
    # Wave 4 (Deep-Reader unification): additive -- THIS call's own flow
    # identity (`bb["flow"]`, the plain-value Source-node id `run_reading_
    # flow` stamps), so a caller re-finding this flow's own SentenceParse/
    # SmEntity nodes afterward (e.g. a document deep-ingest's HeldAnswer
    # bridge) doesn't need to re-derive it. Every existing caller that
    # ignores this new key is byte-unchanged.
    view["flow"] = bb.get("flow")
    return view


def run_produce_over_graph(agent, graph: dict) -> dict:
    """The `produce_analysis(graph=...)` path: the comprehension graph is ALREADY
    built on `agent` (its SmEntity/DiscourseEvent/NarrativeRole/Trope/Theme nodes
    exist) and `graph` is that comprehension view. Seed a produce-analysis Goal +
    ONLY the production stages, then PUMP: `produce_frames` fires on the existing
    Trope nodes, the four section stages on `produce_frames` done — the SAME
    goal-driven fixpoint, no comprehension re-run, no Python section marshalling."""
    s = getattr(agent, "s", agent)
    ad = _LAAdapter(s)
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_driving",))
    _register_cortices(ad)                         # the five cortices + their reflexes
    bb = dict(graph)
    bb.update({"claims": [], "sections": {}})
    ad._master["analysis_bb"] = bb
    _mint_goal(ad, None, produce=True)
    for name in _PRODUCE_STAGES:
        st = ad.s.add_node("AnalysisStage", {"name": name, "status": "pending"})
        ad.inner.add_edge_unchecked(ad.agent, "has_analysis_stage", st)
        _place_in_cortex(ad, st, _CORTEX_OF[name])   # EXECUTIVE cortex
    _tick_reading(ad)                              # TICK to steady state (cortices)
    return bb


# --------------------------------------------------------------------------- #
#  MOVE 2b — COMPREHENSION RECURSES OVER THE StoryUnit TREE. A nested story is
#  recognised as a StoryUnit tree (story_tree, MOVE 2a); each LEAF unit gets its
#  own Source + one `unit_comprehend` AnalysisStage (unit-scoped); the parent
#  gets one `compose` stage. The seeded u_dispatch_* rules fire PER unit stage
#  whose unit-scoped precondition holds -> run_rules RECURSES over the tree for
#  free. NO Python `for unit: comprehend(unit)` loop; the reflex advances ONE
#  stage per firing (the _advance_dispatched_stage precedent), and the fixpoint
#  iterates the units.
# --------------------------------------------------------------------------- #
def _source_text_for_unit(ad, unit_v) -> Optional[str]:
    for n in ad.s.nodes("Source"):
        at = ad.s.node(n)["attrs"]
        if at.get("unit") == unit_v:
            return at.get("text")
    return None


def _story_unit_by_v(ad, unit_v):
    for n in ad.s.nodes("StoryUnit"):
        if _vv(n) == unit_v:
            return n
    return None


def _advance_unit_stage(ad) -> None:
    """The reflex RESPONSE for the nested flow (the I/O boundary, shaped exactly
    like _advance_dispatched_stage): advance ONE dispatched unit stage via its
    named executor, mark it done. A `unit_comprehend` stage comprehends its OWN
    unit in isolation; a `compose` stage composes the parent's spanning theme.
    NO branch on graph state to pick a faculty -- a lookup of which executor the
    stage names, then a mechanical call scoped to the stage's own `unit`."""
    from domains import nested_reading as nr
    from domains import throughlines as thr
    for st in ad.s.nodes("AnalysisStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("status") != "dispatched":
            continue
        name = at.get("name")
        unit_v = at.get("unit")
        if name == "unit_comprehend":
            text = _source_text_for_unit(ad, unit_v)
            if text is not None:
                nr.comprehend_unit(ad, unit_v, text)
            ad.s.set_attr(st, "status", "done")
            return
        if name == "compose":
            parent = _story_unit_by_v(ad, unit_v)
            if parent is not None:
                nr.compose_spanning_theme(ad, parent)
            ad.s.set_attr(st, "status", "done")
            return
        if name == "throughline":
            root = _story_unit_by_v(ad, unit_v)
            if root is not None:
                thr.recognize_throughlines(ad, root)
            ad.s.set_attr(st, "status", "done")
            return
        if name == "meta_theme":
            root = _story_unit_by_v(ad, unit_v)
            if root is not None:
                thr.compose_meta_theme(ad, root)
            ad.s.set_attr(st, "status", "done")
            return
        # unknown stage name in the nested flow -- honest no-op, mark done.
        ad.s.set_attr(st, "status", "done")
        return


def run_nested_reading_flow(agent, text: str, *, max_sentences: int = 40) -> dict:
    """Recognise the StoryUnit tree and comprehend it RECURSIVELY, graph-natively.
    For a depth-1 story (the crow) there are no child units: this returns the
    honest single-unit result WITHOUT changing the flat comprehension (the
    caller uses the existing run_reading_flow for the flat report -- byte-
    identical). For a depth>1 story: mint one Source + one `unit_comprehend`
    stage per LEAF unit + one `compose` stage on the root, then PUMP the seeded
    u_dispatch_* rules + unit_analysis_advance reflex to a fixpoint. The per-unit
    recursion is the rules firing per StoryUnit; the spanning theme emerges as a
    SpanningTheme node. Returns the tree + per-unit views + the composed theme."""
    from domains import story_tree as st_mod
    from domains import nested_reading as nr
    s = getattr(agent, "s", agent)
    ad = _LAAdapter(s)
    tree = st_mod.recognize_story_tree(ad, text, max_sentences=max_sentences)
    leaves = tree.get("children") or []
    out = {"tree": tree, "depth": tree.get("depth"), "units": [],
           "spanning_theme": None}
    if not leaves:
        return out                                  # depth-1: no recursion (flat case).

    nr.ensure_codebook(ad)
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_unit_driving",))
    ad.register_reflex_response("unit_analysis_advance",
                                lambda a: _advance_unit_stage(a))

    # INGEST + STAGES — one Source + one unit_comprehend stage per LEAF unit
    # (unit-scoped), one compose stage on the root. NO faculty order imposed.
    for leaf in leaves:
        uv = leaf["node"]
        src = ad.s.add_node("Source", {"text": " ".join(leaf["sentences"]), "unit": uv})
        stg = ad.s.add_node("AnalysisStage", {"name": "unit_comprehend",
                                              "status": "pending", "unit": uv})
        ad.inner.add_edge_unchecked(ad.agent, "has_analysis_stage", stg)
        parent_node = _story_unit_by_v(ad, uv)     # for_unit -> the leaf itself
        if parent_node is not None:
            ad.inner.add_edge_unchecked(stg, "for_unit", parent_node)
    root_v = tree["root"]["node"]
    root_node = _story_unit_by_v(ad, root_v)
    # the root's cross-unit stages: compose (spanning theme, MOVE 2b) + the
    # THROUGHLINE stages (recognise threads, then compose the whole-story meta-theme
    # from the SET of threads). Each fires on its own graph precondition (compose +
    # throughline when the children are comprehended; meta_theme when the throughline
    # stage is done) -- the seeded u_dispatch_* rules sequence them, no Python order.
    for stage_name in ("compose", "throughline", "meta_theme"):
        stg = ad.s.add_node("AnalysisStage", {"name": stage_name, "status": "pending",
                                              "unit": root_v})
        ad.inner.add_edge_unchecked(ad.agent, "has_analysis_stage", stg)
        if root_node is not None:
            ad.inner.add_edge_unchecked(stg, "for_unit", root_node)

    _tick_reading(ad, max_ticks=400)                 # TICK to steady state (unit cortex)

    for leaf in leaves:
        out["units"].append(nr.read_unit_view(ad, leaf["node"]))
    out["spanning_theme"] = nr.read_spanning_theme(ad, root_node)
    from domains import throughlines as thr
    out["throughlines"] = thr.read_throughlines(ad, root_node)
    out["meta_theme"] = thr.read_meta_theme(ad, root_node)
    return out


__all__ = ["run_reading_flow", "comprehension_result", "_comprehension_view",
           "_LAAdapter", "_advance_dispatched_stage", "run_nested_reading_flow",
           "_advance_unit_stage"]

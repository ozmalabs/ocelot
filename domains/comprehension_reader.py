"""comprehension_reader — THE READ ORCHESTRATOR: six committed comprehension
components, ONE shared graph, in the CORRECT dependency order.

The six comprehension components (situation_model_reader, coref_entities,
inference_generation, discourse_coherence, global_monitoring, character_tom)
are each proven + green in isolation, but two of their inference capabilities
never fired on real narrative because they were sequenced WRONG:

  · GOAL-FROM-STATE (inference_generation.detect_goal_gaps / resolve_goal_gap):
    a character carrying a need-state ('a thirsty crow' -> crow.thirsty) but no
    goal has the goal INFERRED (thirsty -> drink). It reads the SITUATION MODEL,
    so it must run AFTER the spine (situation_model_reader + coref) is built.
  · PHYSICAL-CAUSAL (inference_generation.detect_causal_gaps /
    resolve_causal_gap): two adjacent sentences whose verbs form a physical-
    effect pair (drop a solid -> a level rises) get a `causes` edge between their
    DiscourseEvent nodes. It writes onto discourse_coherence's DiscourseEvent
    graph, so it must run AFTER discourse_coherence.read_discourse has built it —
    else it correctly DEFERS (an honest null on absent nodes).
  · GOAL-ACTION ENABLING CHAIN (this module's own `_mint_goal_action_enabling_
    chain`, below): the SUMMARY read-off (discourse_coherence.centrality_ranking)
    only sees what the DiscourseEvent graph holds. A physical-causal `causes`
    edge alone is often too sparse to out-rank a run of marker-driven "then"/
    "but" `coherence_rel`/`before` edges elsewhere in the same short text (the
    causal HINGE degree-starved relative to orientation/elaboration sentences).
    Trabasso & van den Broek's causal-network model traces the FULL backbone —
    goal -> attempt -> attempt -> outcome — not just the one physical-effect
    link; this pass mints that backbone as `enables` edges (goal sentence ->
    each of the goal-holder's own later action sentences, chained in text
    order) so the centrality graph reflects the STORY's causal structure, not
    only the one physical-effect pair discourse_coherence's own lexical-
    cohesion signal happened to catch. It must run AFTER the goal (step 3) and
    the DiscourseEvent graph (step 4) exist, and its edges must be minted
    BEFORE centrality is computed — the ordering bug this module used to have
    (centrality was read off between steps 4 and 5, before the causal edge
    even existed).

This module is the ONE FUNCTION that threads the six components' PUBLIC entries
onto one shared agent/graph in that order. It SEQUENCES — it makes no
comprehension decision of its own (no if/else deciding meaning): every meaning
decision lives inside a component's own ShapeDecode / rule fixpoint / Argmax.
`_mint_goal_action_enabling_chain` is the one exception worth naming honestly:
it is a mechanical SCAN (which sentence stated the need, which later sentences
the same entity acts in) in the same spirit as inference_generation's own
`detect_goal_gaps`/`detect_causal_gaps` scans — it decides no MEANING (the
goal was already decided by resolve_goal_gap's decode; the sentence order was
already fixed by the text), it only threads already-committed facts into
`enables` edges over an already-existing node type. The order is:

  1+2. ce.read_into_situation_model  — per sentence: mint SmEntity/SmEvent + run
        the situation_model / event_reasoning fixpoint (situation_model_reader,
        called inside), then bind pronouns (coref_entities). ONE whole-text
        driver (the coref-aware superset — see coref_entities' docstring).
  3.   GOAL-FROM-STATE + precondition + bridging inference (inference_generation)
        — reads the situation model built in 1+2.
  4.   dc.read_discourse — build the DiscourseEvent graph (coherence relations;
        centrality is NOT yet computed — the causal/enabling edges below must
        land first).
  5.   PHYSICAL-CAUSAL inference (inference_generation) — NOW the DiscourseEvent
        graph exists, so resolve_causal_gap no longer defers.
  5b.  GOAL-ACTION ENABLING CHAIN (`_mint_goal_action_enabling_chain`, this
        module) — mints the goal -> attempt -> attempt `enables` backbone.
  5c.  CENTRALITY (dc.centrality_ranking) — computed only now, once every
        causal/enabling edge the story implies is on the graph.
  6.   global_monitoring — local incoherence + kinship entailment, per predication.
  7.   character_tom — per-sentence attitude scan (None => factual, no mint).
  8.   RE-RUN the fixpoint — inference minted new facts (goal, part_of, causal
        edges); a final run_rules lets any downstream event_reasoning cascade
        reach fixpoint over the enriched model.
  9.   NARRATIVE STRUCTURE (`narrative_structure.recognize_narrative_structure`)
        — the story-grammar arc (setup/problem/solution/action/consequence/
        resolution), recognised ONE LEVEL UP from discourse coherence, by
        ShapeDecode over a dedicated `ShapeSignatureNarrative` codebook. It
        reads the goal (step 3), the goal-action enabling chain (step 5b) and
        the discourse-coherence pairs (step 4/5) — every fact already decided
        by an earlier component's own collapse — and mints `NarrativeRole`
        nodes tagging each event's story-grammar function. Must run AFTER
        every fact it reads exists, i.e. last.

This is the general 'read a story end-to-end' function. It is NOT crow-specific:
any short narrative ('The wolf was hungry. It saw a lamb. It chased the lamb.')
reads into a coherent situation model + inferred goal + discourse graph, and
the SAME goal-action enabling scan applies (no fable string is named anywhere
in `_mint_goal_action_enabling_chain`).

ARCHITECTURE (CLAUDE.md). The orchestrator is a WORLD-ADAPTER read path: it only
calls the six components' public entries and threads their output onto one graph.
No agent decision lives here — no if/else selects a meaning, no Python picks a
winner, no rule engine runs in Python. Every DECISION is a component's own
(ShapeDecode, the run_rules fixpoint, the Argmax) — the ONE enabling-chain scan
decides no meaning, only replays already-fixed sentence order (see above). No
`import re`.
"""
from __future__ import annotations

from typing import Any

from domains import character_tom as ctom
from domains import coref_entities as ce
from domains import dictionary_lexicon as dl
from domains import discourse_coherence as dc
from domains import global_monitoring as gm
from domains import inference_generation as ig
from domains import narrative_structure as ns
from domains import reading_collapse as rc
from domains import reading_review as rr
from domains import trope_theme as tt


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


# --------------------------------------------------------------------------- #
#  GOAL -> ACTION ENABLING CHAIN — mechanical scan (no new meaning decided),
#  mints `enables` edges over the ALREADY-BUILT DiscourseEvent graph. General:
#  no fable string is named; every input (goal, entity, sentence order) is
#  read off graph data already committed by other components' own decisions.
# --------------------------------------------------------------------------- #
_PROPERTY_RELS = ("is_a", "is", "cop")


def _sentence_ingest_slices(textbase: list, ingests: list) -> list:
    """[[ingest_record, ...], ...] — one slice per sentence. `ingests` is a
    flat, IN-ORDER list of one record per predication across the whole text
    (coref_entities.read_into_situation_model's own `turn` counter, one turn
    per predication); `textbase[i]['predications']` holds sentence i's own
    predication COUNT. Slicing `ingests` by that count replays the SAME
    accounting the spine already did — no re-parse, no new decision, just
    recovering which already-recorded ingest record belongs to which
    sentence."""
    slices = []
    cum = 0
    for tb in textbase:
        k = len(tb.get("predications") or [])
        slices.append(ingests[cum:cum + k])
        cum += k
    return slices


def _discourse_node_by_order(sub, order: int, unit=None):
    """FLOW-SCOPED (Wave 1A, mirrors nested_reading's `unit` convention): a bare
    `order` alone collides across two flows on a persistent substrate (each
    flow's DiscourseEvent orders start back at 0) — `unit=None` is the
    byte-identical legacy (whole-graph) lookup."""
    for n in sub.nodes("DiscourseEvent"):
        at = sub.node(n)["attrs"]
        if at.get("order") == order and (unit is None or at.get("unit") == unit):
            return n
    return None


def _mint_goal_action_enabling_chain(agent, textbase: list, ingests: list,
                                     goal: list, unit=None) -> list:
    """Trabasso & van den Broek's causal-network BACKBONE (goal -> attempt ->
    attempt -> ... ), one level up from inference_generation's single
    physical-effect `causes` link. For every MINTED goal (inference_
    generation.resolve_goal_gap's own decode — reused, not re-decided; this
    scan invents no new need/remedy fact): locate the sentence that stated
    the entity's need (the SAME predication `resolve_goal_gap`'s `need_attr`
    names — a mechanical read off the ingest records already produced by
    situation_model_reader/coref_entities, not a new parse), then every LATER
    sentence whose own (coref-RESOLVED) predication's subject is that SAME
    entity and whose relation is not a bare property statement — the
    entity's own subsequent actions/attempts, in the order the text tells
    them. Mints an `enables` edge from the goal sentence to the first action,
    then chains each action to the next — the goal-pursuit causal structure,
    read off already-decided facts (the goal, the protagonist index, sentence
    order), never a fable-specific narrative template. Returns
    [{entity, goal_sentence, action_sentences, edges}] for callers to inspect."""
    sub, native = _resolve(agent)
    slices = _sentence_ingest_slices(textbase, ingests)
    chains = []
    for g in goal:
        if not g.get("minted"):
            continue
        entity_name = g["gap"]["entity"]
        need_attr = g["gap"]["need_attr"]
        goal_idx = None
        for i, recs in enumerate(slices):
            for rec in recs:
                pred = rec.get("predication") or []
                if (len(pred) >= 3 and str(pred[0]) in _PROPERTY_RELS
                        and str(pred[1]) == entity_name and str(pred[2]) == need_attr):
                    goal_idx = i
                    break
            if goal_idx is not None:
                break
        if goal_idx is None:
            chains.append({"entity": entity_name, "goal_sentence": None,
                           "action_sentences": [], "edges": [],
                           "note": "goal-establishing sentence not found -- honest skip"})
            continue
        action_idxs = []
        for i in range(goal_idx + 1, len(slices)):
            for rec in slices[i]:
                pred = rec.get("predication") or []
                if (len(pred) >= 2 and str(pred[0]) not in _PROPERTY_RELS
                        and str(pred[1]) == entity_name):
                    action_idxs.append(i)
                    break
        prev_idx = goal_idx
        edges = []
        for idx in action_idxs:
            a = _discourse_node_by_order(sub, prev_idx, unit=unit)
            b = _discourse_node_by_order(sub, idx, unit=unit)
            if a is not None and b is not None:
                dc._mint_edge(sub, native, a, b, "enables",
                              {"source": "goal_action_chain", "entity": entity_name})
                edges.append({"from": prev_idx, "to": idx})
            prev_idx = idx
        chains.append({"entity": entity_name, "goal_sentence": goal_idx,
                       "action_sentences": action_idxs, "edges": edges})
    # GENERIC EVENT-SEQUENCE BACKBONE (2026-07-07): a goalless narrative (a mercy/
    # rescue tale — no need-state, so no want-SmEvent, so no goal-anchored chain)
    # still HAS an arc: the protagonist's own sequence of EVENTIVE actions. When no
    # goal minted a chain, build one per event-agent off the event sequence, so the
    # arc fills from the real events rather than staying empty. A story WITH a
    # minted goal never reaches this branch -> its report is byte-identical. It
    # decides no meaning (the eventive-vs-stative split is WordNet's; the story-
    # grammar ROLE is still the ShapeDecode's verdict downstream) — it only replays
    # already-fixed sentence order into `enables` edges over existing nodes.
    if not any(g.get("minted") for g in goal):
        chains = _mint_event_sequence_enabling_chain(agent, sub, native, slices, unit=unit)
    return chains


def _mint_event_sequence_enabling_chain(agent, sub, native, slices: list, unit=None) -> list:
    """The goalless backbone: for each entity that is the SUBJECT of an EVENTIVE
    predication (WordNet-classified via situation_model_reader.eventive_membership —
    not a seeded verb list), its FIRST such sentence is the arc's opening slot and
    each LATER such sentence an action, chained by `enables` edges (the SAME
    mechanical scan the goal path uses, minus the goal anchor). One chain per
    protagonist, in text order. No meaning decided here — WordNet says which verbs
    are eventive, the arc decode says which role each slot plays."""
    from domains import situation_model_reader as smr
    order_by_agent: dict = {}
    for i, recs in enumerate(slices):
        for rec in recs:
            pred = rec.get("predication") or []
            if len(pred) < 2:
                continue
            rel, subj = str(pred[0]), str(pred[1])
            if rel in _PROPERTY_RELS:
                continue
            if not smr.eventive_membership(agent, rel)["eventive"]:
                continue
            order_by_agent.setdefault(subj, [])
            if i not in order_by_agent[subj]:
                order_by_agent[subj].append(i)
    chains = []
    for entity_name, idxs in order_by_agent.items():
        idxs = sorted(idxs)
        goal_idx, action_idxs = idxs[0], idxs[1:]
        prev_idx = goal_idx
        edges = []
        for idx in action_idxs:
            a = _discourse_node_by_order(sub, prev_idx, unit=unit)
            b = _discourse_node_by_order(sub, idx, unit=unit)
            if a is not None and b is not None:
                dc._mint_edge(sub, native, a, b, "enables",
                              {"source": "event_sequence_chain", "entity": entity_name})
                edges.append({"from": prev_idx, "to": idx})
            prev_idx = idx
        chains.append({"entity": entity_name, "goal_sentence": goal_idx,
                       "action_sentences": action_idxs, "edges": edges,
                       "source": "event_sequence"})
    return chains


def read_and_comprehend(agent, text: str, *, window: int = 2,
                        max_sentences: int = 40, stages=None,
                        register=None) -> dict:
    """Read `text` end-to-end and return every intermediate comprehension record
    (spine / gaps / resolutions / discourse / centrality / monitoring / tom /
    narrative arc / tropes) so a caller can query the graph back out.

    GOAL-DRIVEN (2026-07, the migration): the 10 hand-sequenced faculty calls
    this function used to BE are DELETED. It now seeds a `comprehend` Goal + the
    source and runs the comprehension FIXPOINT (`reading_drive.run_reading_flow`
    over seeds/literary_analysis_driving.json): each faculty fires from its OWN
    graph precondition and `run_rules` sequences them by data-dependency. This
    function makes NO comprehension decision and imposes NO order — it is a thin
    world-adapter call (there is deliberately no `if`/`else` in its body: the
    ordering that used to live here is now the seed's dispatch rules).

    `stages` (Wave 2, the APERTURE): an optional subset of the ten comprehension
    stage names to mint (`reading_drive._COMPREHENSION_STAGES`) — a pure pass-
    through to `run_reading_flow`. `None` (every existing caller) mints all ten,
    byte-identical. A caller that only needs a LIGHT read (e.g. a chat-turn
    shadow read) passes a narrower list read off a register's own `stages`
    attr (`register_source._aperture_attrs`) so faculties outside the subset
    never fire and never pay their `ensure_seeds`/`ensure_codebook` cost.

    `register` (Wave: foveation-as-hint): the register name that hinted this
    aperture, a pure pass-through to `run_reading_flow`/`_mint_goal` so the
    seeded `escalate_*` rules can look up this flow's own `ApertureBudget`.
    `None` (every pre-wave caller) normalises to `'default'`."""
    from domains import reading_drive as rd
    return rd.comprehension_result(agent, text, window=window,
                                   max_sentences=max_sentences, stages=stages,
                                   register=register)


__all__ = ["read_and_comprehend"]

"""Block 345000 — rung 3: the AUTOPOIETIC LOOP, closed over ALREADY-HELD knowledge.

The generation arc built the pieces: a communicative goal (341), voice/complexity
over a choosable audience (342), the self-conditioned rollout (343), and the
grammar-owned plan-then-realize clause (344). This module CLOSES THE LOOP so the
entity converses with ITSELF with no external teacher in the cycle:

    curiosity SELECTS a topic  (a filed SelfConcern{kind:'knowledge', content:T})
      -> SELF-ANSWER T from HELD knowledge  (read T's is-a out-edges off the graph,
         realize an ordered grammatical clause via the teacher-free producer)
      -> MONITOR  (score_self_target parse-back: did the saying recover the content?)
      -> RESIDUAL  (missing/uncovered concepts) -> ENQUEUE as the next SelfConcern
      -> back to SELECT.

HONEST BOUND (load-bearing, not hidden): the self-answer is DERIVED from held graph
edges. A topic the agent holds NO knowledge about has nothing to derive from — the
loop does NOT fabricate. For such a topic the faithful action is still the EXTERNAL
ASK (question_driver / pack.ask) — the teacher floor. So this is a CLOSED loop over
ALREADY-HELD knowledge; genuinely-unknown topics require external input. On
no-held-knowledge the caller CHOOSES (a parameter, not hardwired) whether to just
RETURN the residual or INVOKE an external ask_fn — the choice point stays open.

Additive: builds only ON existing teacher-free primitives (llm_knowledge_seed read-off,
literary_analysis._build_producer, predictive_reading.realize_goal_clause,
self_target_monitor.score_self_target). Never edits a protected file or the .so, never
touches conceptualizer.py. No LLM at loop time (query is substrate-only; the producer
grounds via teacher_stub).
"""
from __future__ import annotations

from typing import Any, Callable, Optional


# --------------------------------------------------------------------------- #
#  resolve the substrate handle the way the other domains do (wa may be a world
#  adapter, a substrate, or carry one).
# --------------------------------------------------------------------------- #
def _sub(wa):
    for attr in ("s", "substrate", "sub"):
        cand = getattr(wa, attr, None)
        if cand is not None and hasattr(cand, "nodes"):
            return cand
    if hasattr(wa, "nodes"):
        return wa
    raise TypeError("self_dialogue: cannot resolve a substrate from %r" % (wa,))


def _find_concept(sub, name):
    # WorldAdapter's graph facade stores the native substrate on `_inner`;
    # direct substrate providers may expose the indexed lookup themselves.
    # Use the maintained exact-name index when available, while retaining the
    # generic scan fallback for minimal graph implementations.
    index = getattr(sub, "_inner", sub)
    nodes_where = getattr(index, "nodes_where", None)
    has_index = getattr(index, "has_attr_index", None)
    declare_index = getattr(index, "declare_attr_index", None)
    if callable(nodes_where) and callable(has_index) and callable(declare_index):
        if not has_index("Concept", "name"):
            declare_index("Concept", "name")
        matches = nodes_where("Concept", "name", str(name))
        return matches[0] if matches else None
    for c in sub.nodes("Concept"):
        if sub.node(c)["attrs"].get("name") == str(name):
            return c
    return None


def _agent_node(sub):
    for a in sub.nodes("Agent"):
        return a
    return None


# --------------------------------------------------------------------------- #
#  1. SELECT — the loop entry: the agent's own filed knowledge concerns.
# --------------------------------------------------------------------------- #
def select_curiosity_topic(wa) -> Optional[str]:
    """Return the topic string of an un-retired knowledge SelfConcern the agent
    has filed (mirrors reflective_faculty._run_self_gaps' read). None if none.
    This is what curiosity autonomously chose to pursue."""
    sub = _sub(wa)
    for sc in sub.nodes("SelfConcern"):
        a = sub.node(sc)["attrs"]
        if a.get("kind") == "knowledge" and a.get("status") != "retired":
            content = a.get("content")
            if content:
                return str(content)
    return None


def _existing_concern_contents(sub) -> set:
    out = set()
    for sc in sub.nodes("SelfConcern"):
        a = sub.node(sc)["attrs"]
        if a.get("status") != "retired" and a.get("content"):
            out.add(str(a.get("content")))
    return out


# --------------------------------------------------------------------------- #
#  2. DERIVE — read the topic's HELD is-a edges off the graph into goal frames.
# --------------------------------------------------------------------------- #
def held_frames_for_topic(wa, topic: str) -> list[dict]:
    """The goal frames DERIVABLE from what the agent already holds about `topic`:
    its direct is-a out-edges (causal_influence, relation attr = 'isa' in a
    knowledge_isa Microtheory). Each becomes a copular frame the grammar realizes:
    isa(topic, X) -> {event:'is', agent:topic, patient:X, tense:'present',
    intent:'inform'}. Returns [] when the agent holds nothing about the topic (the
    honest empty — nothing to derive, no fabrication). Substrate-only, no LLM."""
    sub = _sub(wa)
    node = _find_concept(sub, topic)
    if node is None:
        return []
    frames = []
    for k in sub.neighbours(node, "causal_influence"):
        obj = sub.node(k)["attrs"].get("name")
        if obj and obj != topic:
            frames.append({"event": "is", "agent": str(topic), "patient": str(obj),
                           "tense": "present", "intent": "inform"})
    return frames


def held_graph_frame_for_topic(wa, topic: str) -> tuple[dict | None, list[str]]:
    """Return the first graph-derived frame and its concept path.

    This is the condensed inner-speech read: it follows graph structure directly
    and does not create a clause or invoke the covert monitor.  The path is kept
    as explicit node names so callers can compute trajectory residuals without
    parsing an English surface back into concepts.
    """
    sub = _sub(wa)
    node = _find_concept(sub, topic)
    if node is None:
        return None, [str(topic)]
    for child in sub.neighbours(node, "causal_influence"):
        obj = sub.node(child)["attrs"].get("name")
        if obj and obj != topic:
            return ({"event": "is", "agent": str(topic), "patient": str(obj),
                     "tense": "present", "intent": "inform"},
                    [str(topic), str(obj)])
    return None, [str(topic)]


# --------------------------------------------------------------------------- #
#  3. SELF-ANSWER — graph-read by default; realize only when requested.
# --------------------------------------------------------------------------- #
def self_answer(wa, topic: str, *, on_unknown: str = "return",
                ask_fn: Optional[Callable[[str], Any]] = None,
                language: str = "en", realize: bool = True) -> dict[str, Any]:
    """Answer `topic` from HELD knowledge, optionally via the grammar-owned
    realizer, teacher-free. With ``realize=False`` this is a graph-only read for
    an intermediate inner-speech hop. Returns
        {answered: bool, topic, surface, verdict, residual, frame, source,
         reason?}
    where `verdict` is score_self_target's parse-back and `residual` = the
    concepts the saying failed to recover (verdict['missing']) or [topic] when
    nothing was held.

    NO held knowledge => answered False, reason 'no_held_knowledge'. What happens
    then is the CALLER'S CHOICE via `on_unknown` (NOT hardwired):
      · 'return' (default): return the residual [topic]; the caller decides.
      · 'ask'   : invoke `ask_fn(topic)` (the external floor — question_driver /
        pack.ask), record its result under `source='external_ask'`. If no ask_fn
        is supplied, behaves as 'return' (nothing to invoke).
    The teacher is invoked ONLY on this branch and ONLY when on_unknown=='ask'."""
    frame, graph_path = held_graph_frame_for_topic(wa, topic)
    if frame is None:
        res = {"answered": False, "topic": topic, "surface": "",
               "verdict": None, "residual": [topic], "frame": None,
               "reason": "no_held_knowledge", "source": "held",
               "graph_path": graph_path, "recovered": []}
        if on_unknown == "ask" and ask_fn is not None:
            asked = ask_fn(topic)
            res["source"] = "external_ask"
            res["external_answer"] = asked
        return res

    # Inner trajectory hops stop here: graph state is sufficient to select the
    # next topic, and no intermediate English clause is produced or parsed.
    if not realize:
        return {"answered": True, "topic": topic, "surface": "",
                "verdict": None, "residual": [], "frame": frame,
                "source": "held", "mode": "graph",
                "graph_path": graph_path, "recovered": graph_path}

    from domains import literary_analysis as la
    from domains import predictive_reading as pr
    sub = _sub(wa)
    producer = la._build_producer([frame])  # teacher-free (teacher_stub, no LLM)
    r = pr.realize_goal_clause(sub, producer, frame,
                               intended_concepts=[frame["agent"], frame["patient"]],
                               language=language, allow_fallback=False)
    verdict = r.get("verdict") or {}
    residual = list(verdict.get("missing") or [])
    return {"answered": bool(r.get("surface")), "topic": topic,
            "surface": r.get("surface", ""), "verdict": verdict,
            "residual": residual, "frame": frame, "source": "held",
            "mode": r.get("mode"), "graph_path": graph_path,
            "recovered": sorted(set(graph_path) | set(verdict.get("recovered") or []))}


# --------------------------------------------------------------------------- #
#  4. ENQUEUE — the residual becomes the next gap (closes back to SELECT).
# --------------------------------------------------------------------------- #
def enqueue_residual(wa, residual, *, dedup: bool = True) -> list:
    """File each residual concept as a new knowledge SelfConcern (mirrors
    lp_mint_topic_gap's minted node + the engineering_residual_ingest write
    precedent), so what the saying could NOT recover becomes the next thing to
    pursue. Dedups against existing un-retired concern contents. Returns the new
    node ids."""
    sub = _sub(wa)
    agent = _agent_node(sub)
    existing = _existing_concern_contents(sub) if dedup else set()
    new_ids = []
    for concept in residual or []:
        c = str(concept)
        if dedup and c in existing:
            continue
        try:
            sc = sub.add_node("SelfConcern", {"status": "noted",
                                              "source": "implicit",
                                              "kind": "knowledge", "content": c})
        except Exception:
            continue
        existing.add(c)
        new_ids.append(sc)
        if agent is not None:
            try:
                sub.add_edge_unchecked(agent, "has_self_concern", sc)
            except Exception:
                pass
    return new_ids


# --------------------------------------------------------------------------- #
#  5. ONE STEP — select -> self-answer -> enqueue residual.
# --------------------------------------------------------------------------- #
def run_autopoietic_step(wa, *, topic: Optional[str] = None,
                         on_unknown: str = "return",
                         ask_fn: Optional[Callable[[str], Any]] = None,
                         enqueue: bool = True) -> dict[str, Any]:
    """One turn of the loop: SELECT a topic (or use the given `topic`), SELF-ANSWER
    it from held knowledge, and ENQUEUE the residual as the next gap. Returns a
    record {topic, surface, answered, verdict, residual, enqueued, source,
    teacher_called}. teacher_called is True only if the no-held-knowledge branch
    actually invoked ask_fn (on_unknown=='ask')."""
    chosen = topic or select_curiosity_topic(wa)
    if not chosen:
        return {"topic": None, "surface": "", "answered": False,
                "verdict": None, "residual": [], "enqueued": [],
                "source": None, "teacher_called": False,
                "reason": "no_topic_selected"}
    ans = self_answer(wa, chosen, on_unknown=on_unknown, ask_fn=ask_fn)
    enqueued = enqueue_residual(wa, ans.get("residual")) if enqueue else []
    return {"topic": chosen, "surface": ans.get("surface", ""),
            "answered": ans.get("answered", False),
            "verdict": ans.get("verdict"), "residual": ans.get("residual", []),
            "enqueued": enqueued, "source": ans.get("source"),
            "reason": ans.get("reason"),
            "teacher_called": ans.get("source") == "external_ask"}

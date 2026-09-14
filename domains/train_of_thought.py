"""Block 346000 — the TRAIN OF THOUGHT: an UNSPOKEN CONVERSATION WITH YOURSELF.

A train of thought is not a retrieval loop run N times. It is the goal-directed,
audience-targeted, self-monitored utterance machinery of rungs 341-345 turned INWARD
(Vygotsky's inner speech): target = self, audience = self, articulation COVERT — the
clause is realized and HEARD (parsed back) but never emitted as overt speech.

A TURN is one exchange in that inner conversation:
  · SPEAKER-SELF says a covert clause about the current topic (self_dialogue.self_answer
    -> realize_goal_clause; the surface is produced but routed nowhere overt);
  · LISTENER-SELF hears it (score_self_target parse-back inside self_answer): what did
    the saying recover, what is the RESIDUAL (what listener-self failed to recover)?
The CONVERSATION is turns chained: speaker/listener-self alternating, each turn
conditioned on the prior self-utterance and its residual. What drives the NEXT turn is a
PLUGGABLE STANCE over (prev_turn, seen) — the core stance is 'residual' (pursue what
didn't land + the transitively-implied neighbours); later stances (question / disagree /
elaborate) plug into the SAME seam.

DEEPENING (what speaker-self reaches for when a plain self-restatement leaves residual):
  · cone  — transitive is-a closure (grounded_representation.cone over causal_influence):
    teacher-free on the plain is-a seed, the always-available reasoning floor (poodle ->
    dog -> mammal -> organism). This is genuine transitive inference, not retrieval.
  · order_n / dimension-mint — OPT-IN flags, OFF by default and honest-gated: they need
    richer held structure (structural-property definitions; seeds/qualia_space.json +
    typed edges + the collapse/residual loop) than the plain is-a seed provides. Left as
    hooks, not faked. (Their own properly-seeded block comes later.)

HONEST BOUNDS (inherited from block 345, enforced): the conversation runs over ALREADY-
HELD knowledge; a topic with nothing held does NOT fabricate — the external ASK floor
remains, choosable via on_unknown. No teacher in the loop on the held path.

Additive: composes self_dialogue + grounded_representation; never edits a protected file
or the .so, never touches conceptualizer.py. Teacher-free at loop time (no LLM).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from domains import self_dialogue as sd


# --------------------------------------------------------------------------- #
#  transitive-reasoning escalation: the is-a cone beyond the direct edges.
# --------------------------------------------------------------------------- #
def transitive_ancestors(wa, topic: str) -> list[str]:
    """The is-a ancestors of `topic` BEYOND its direct edges — the transitive
    closure (grounded_representation.cone over causal_influence) minus the topic
    itself and its already-direct objects. Teacher-free graph read; this is what
    speaker-self can DERIVE (transitive inference) rather than retrieve."""
    sub = sd._sub(wa)
    node = sd._find_concept(sub, topic)
    if node is None:
        return []
    try:
        from domains import grounded_representation as gr
        cone = gr.cone(sub, node, edge_type="causal_influence")
    except Exception:
        return []
    direct = {sub.node(k)["attrs"].get("name")
              for k in sub.neighbours(node, "causal_influence")}
    out = []
    for n in cone:
        nm = sub.node(n)["attrs"].get("name")
        if nm and nm != topic and nm not in direct:
            out.append(nm)
    return out


# --------------------------------------------------------------------------- #
#  the PLUGGABLE STANCE — what listener-self does with a heard turn to drive the
#  next one. The core stance is 'residual'; richer stances (question/disagree/
#  elaborate) implement the SAME (turn, seen) -> list[next_topic] interface.
# --------------------------------------------------------------------------- #
def residual_stance(wa, turn: dict, seen: set) -> list[str]:
    """Default stance: the next things to think about are (a) what listener-self
    failed to recover (the residual), plus (b) the transitively-implied ancestors
    of the topic just thought (the is-a cone) — the natural continuation of the
    train ('poodle is a dog... and a dog is a mammal...'). Excludes already-seen
    topics so the train MOVES rather than loops."""
    nxt: list[str] = []
    for c in (turn.get("residual") or []):
        if c not in seen and c != turn.get("topic"):
            nxt.append(c)
    for anc in transitive_ancestors(wa, turn.get("topic", "")):
        if anc not in seen and anc not in nxt:
            nxt.append(anc)
    return nxt


_STANCES: dict[str, Callable[[Any, dict, set], list[str]]] = {
    "residual": residual_stance,
}


# --------------------------------------------------------------------------- #
#  ONE covert TURN — speaker-self says (covertly), listener-self hears.
# --------------------------------------------------------------------------- #
def inner_turn(wa, topic: str, *, on_unknown: str = "return",
               ask_fn: Optional[Callable[[str], Any]] = None) -> dict[str, Any]:
    """One turn of the inner conversation: a COVERT self-utterance about `topic`
    (self_dialogue.self_answer realizes + parse-backs the clause; the surface is
    HEARD by listener-self but never emitted as overt speech — inner speech), and
    the residual listener-self failed to recover.

    Returns {topic, inner_utterance, answered, verdict, residual, source, covert}.
    `inner_utterance` is the covert clause (labelled covert=True to make explicit
    it is inner speech — never routed to an overt output sink)."""
    ans = sd.self_answer(wa, topic, on_unknown=on_unknown, ask_fn=ask_fn)
    return {"topic": topic,
            "inner_utterance": ans.get("surface", ""),   # covert: heard, not spoken
            "covert": True,
            "answered": ans.get("answered", False),
            "verdict": ans.get("verdict"),
            "residual": ans.get("residual", []),
            "source": ans.get("source"),
            "reason": ans.get("reason")}


# --------------------------------------------------------------------------- #
#  THE CONVERSATION — chain covert turns, next driven by the pluggable stance.
# --------------------------------------------------------------------------- #
def run_inner_conversation(wa, *, topic: Optional[str] = None,
                           max_turns: int = 8, stance: str = "residual",
                           stance_fn: Optional[Callable[[Any, dict, set], list[str]]] = None,
                           on_unknown: str = "return",
                           ask_fn: Optional[Callable[[str], Any]] = None,
                           enqueue: bool = True) -> dict[str, Any]:
    """Run the inner unspoken conversation: pick a starting topic (given or from a
    filed knowledge SelfConcern), then chain covert turns — each turn's next topics
    chosen by the STANCE over (turn, seen). The train MOVES via the residual +
    transitive cone until it runs out of fresh topics, stalls, or hits max_turns.

    Deeper faculties (order_n / dimension-mint) are OPT-IN and honest-gated; this
    core uses the always-available transitive cone. Enqueue files unresolved
    residual as SelfConcerns (block-345 loop) so the train persists across sessions.

    Returns {turns:[turn...], topics_thought:[...], stop_reason, frontier_growth:
    [len per turn], teacher_called:bool}."""
    stance_fn = stance_fn or _STANCES.get(stance, residual_stance)
    start = topic or sd.select_curiosity_topic(wa)
    if not start:
        return {"turns": [], "topics_thought": [], "stop_reason": "no_topic",
                "frontier_growth": [], "teacher_called": False}

    seen: set = set()
    agenda: list[str] = [start]
    turns: list[dict] = []
    frontier_growth: list[int] = []
    teacher_called = False
    stop_reason = "max_turns"

    for _ in range(int(max_turns)):
        # pick the next un-thought topic from the agenda (train MOVES, no re-loop)
        cur = None
        while agenda:
            cand = agenda.pop(0)
            if cand not in seen:
                cur = cand
                break
        if cur is None:
            stop_reason = "converged"        # agenda exhausted — nothing left to think
            break
        seen.add(cur)

        turn = inner_turn(wa, cur, on_unknown=on_unknown, ask_fn=ask_fn)
        turns.append(turn)
        if turn.get("source") == "external_ask":
            teacher_called = True

        # LISTENER-SELF drives the next turn(s) via the stance.
        nxt = stance_fn(wa, turn, seen)
        for t in nxt:
            if t not in seen and t not in agenda:
                agenda.append(t)
        frontier_growth.append(len(agenda))

        # persist unresolved residual as gaps (block-345), so the train continues later
        if enqueue and turn.get("residual"):
            sd.enqueue_residual(wa, [c for c in turn["residual"] if c not in seen])

    return {"turns": turns,
            "topics_thought": [t["topic"] for t in turns],
            "stop_reason": stop_reason,
            "frontier_growth": frontier_growth,
            "teacher_called": teacher_called}

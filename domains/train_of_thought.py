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
#  ATTENTION-WIDTH — the transition-breadth axis. This is the GRAPH-WALK ANALOGUE
#  of aperture, and a DISTINCT axis from it: the substrate's `aperture`
#  (observer_aperture resolves/grain) governs the RESOLUTION of a readout over a
#  signature FIELD; attention_width governs the BREADTH of the neighbourhood a
#  train of thought admits as its next transitions over the concept GRAPH. Both
#  are a narrow<->wide dial, but they live in different spaces — so this is named
#  distinctly and does NOT touch resolves/grain.
#
#  The axis realizes the deliberate<->associative CONTINUUM (Christoff et al.):
#    width ~ 0  narrow / GOAL-DIRECTED  — residual + is-a ancestors only (the
#               deliberately-constrained regime; == residual_stance, the default);
#    width mid  add is-a CHILDREN (hyponyms) + SIBLINGS (co-children of a parent);
#    width ~ 1  wide / ASSOCIATIVE — any-relation neighbours (spreading activation
#               over _DEFAULT_REL_EDGES), James's transitive/associative flights.
#  'Could it be both?' — yes: goal-directed and associative are the two ENDS of
#  one adjustable axis, not two stances.
# --------------------------------------------------------------------------- #
def _children(sub, node) -> list[str]:
    """is-a hyponyms: the in-neighbours over causal_influence (dog -> poodle,
    beagle). The downward associative step."""
    try:
        return [sub.node(k)["attrs"].get("name")
                for k in sub.in_neighbours(node, "causal_influence")]
    except Exception:
        return []


def _siblings(sub, node, topic: str) -> list[str]:
    """concepts sharing a parent with `topic` (co-children) — the lateral
    associative step (poodle ~ beagle, both is-a dog)."""
    out: list[str] = []
    try:
        for p in sub.neighbours(node, "causal_influence"):     # topic's parents
            for c in sub.in_neighbours(p, "causal_influence"):  # their children
                nm = sub.node(c)["attrs"].get("name")
                if nm and nm != topic:
                    out.append(nm)
    except Exception:
        pass
    return out


def _relation_neighbours(sub, node, topic: str) -> list[str]:
    """the WIDE associative frontier: neighbours over the full relation edge-class
    set (reuse analogy_search._DEFAULT_REL_EDGES rather than reinvent) in both
    directions — spreading activation over the graph, not just the is-a spine."""
    out: list[str] = []
    try:
        from domains.analogy_search import _DEFAULT_REL_EDGES as REL
    except Exception:
        REL = ("causal_influence", "has_part", "part_of", "made_of", "member_of")
    for et in REL:
        try:
            for k in sub.neighbours(node, et):
                nm = sub.node(k)["attrs"].get("name")
                if nm and nm != topic:
                    out.append(nm)
        except Exception:
            pass
        try:
            for k in sub.in_neighbours(node, et):
                nm = sub.node(k)["attrs"].get("name")
                if nm and nm != topic:
                    out.append(nm)
        except Exception:
            pass
    return out


def breadth_stance(width: float) -> Callable[[Any, dict, set], list[str]]:
    """A graded stance at attention-width `width` in [0,1]. width 0 is byte-for-
    byte the goal-directed residual_stance; as width rises the admitted transition
    neighbourhood widens (children + siblings, then any-relation associative
    neighbours). The next topics are ordered goal-first so a mid-width train stays
    anchored while it also wanders."""
    w = max(0.0, min(1.0, float(width)))

    def _stance(wa, turn: dict, seen: set) -> list[str]:
        topic = turn.get("topic", "")
        nxt: list[str] = []

        def _add(items):
            for c in items:
                if c and c not in seen and c != topic and c not in nxt:
                    nxt.append(c)

        # width 0..1 always includes the goal-directed core (residual + ancestors)
        _add(c for c in (turn.get("residual") or []))
        _add(transitive_ancestors(wa, topic))
        if w <= 0.0:
            return nxt

        sub = sd._sub(wa)
        node = sd._find_concept(sub, topic)
        if node is None:
            return nxt
        # mid width: lateral/downward associative steps (children + siblings)
        if w >= 0.34:
            _add(_children(sub, node))
            _add(_siblings(sub, node, topic))
        # wide width: full associative spreading over the relation edge-classes
        if w >= 0.67:
            _add(_relation_neighbours(sub, node, topic))
        return nxt

    return _stance


# convenience named points on the axis (still one axis — these are just labels)
def goal_stance(wa, turn, seen):        # width 0
    return breadth_stance(0.0)(wa, turn, seen)


def associative_stance(wa, turn, seen):  # width 1
    return breadth_stance(1.0)(wa, turn, seen)


_STANCES["goal"] = goal_stance
_STANCES["associative"] = associative_stance


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
                           max_turns: int = 8, stance: Optional[str] = None,
                           stance_fn: Optional[Callable[[Any, dict, set], list[str]]] = None,
                           width: float = 0.0,
                           novelty_window: Optional[int] = 3,
                           on_unknown: str = "return",
                           ask_fn: Optional[Callable[[str], Any]] = None,
                           enqueue: bool = True) -> dict[str, Any]:
    """Run the inner unspoken conversation: pick a starting topic (given or from a
    filed knowledge SelfConcern), then chain covert turns — each turn's next topics
    chosen by the STANCE over (turn, seen).

    ATTENTION-WIDTH: `width` in [0,1] sets the transition breadth on the goal<->
    associative axis (0 = goal-directed / is-a spine, 1 = wide associative). It is
    used when neither `stance` nor `stance_fn` is given (the honest default width 0
    == the block-346 residual_stance, backward-compatible). An explicit `stance`
    name or `stance_fn` overrides the width axis.

    HONEST TERMINATION (a dynamic on the axis, not a bolted-on rule): the train
    disengages when the last `novelty_window` turns recovered NOTHING new (novelty
    stalled) — the anti-rumination stop (a train circling without learning lets go),
    stop_reason='novelty_stalled'. Set novelty_window=None to disable (pure agenda-
    exhaustion, the block-346 behavior). [Richer upgrade, noted: drive this from the
    learning_progress_curiosity smoothed_progress signal instead of the novelty
    proxy.]

    Returns {turns, topics_thought, stop_reason, frontier_growth, teacher_called,
    width, recovered_total}."""
    if stance_fn is None:
        stance_fn = _STANCES.get(stance) if stance else None
    if stance_fn is None:
        stance_fn = breadth_stance(width)      # the width axis (0 == residual_stance)
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
    recovered_total: set = set()          # every concept the train has recovered
    no_novelty_run = 0                    # consecutive turns that recovered nothing new

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

        # NOVELTY: what did this turn RECOVER that the train had not held before?
        rec = set((turn.get("verdict") or {}).get("recovered") or [])
        fresh = rec - recovered_total
        recovered_total |= rec
        no_novelty_run = 0 if fresh else (no_novelty_run + 1)

        # LISTENER-SELF drives the next turn(s) via the stance.
        nxt = stance_fn(wa, turn, seen)
        for t in nxt:
            if t not in seen and t not in agenda:
                agenda.append(t)
        frontier_growth.append(len(agenda))

        # persist unresolved residual as gaps (block-345), so the train continues later
        if enqueue and turn.get("residual"):
            sd.enqueue_residual(wa, [c for c in turn["residual"] if c not in seen])

        # HONEST TERMINATION (dynamic on the axis): disengage when the last
        # `novelty_window` turns recovered nothing new — the train is circling
        # without learning (anti-rumination), so it lets go rather than churn.
        if novelty_window and no_novelty_run >= int(novelty_window):
            stop_reason = "novelty_stalled"
            break

    return {"turns": turns,
            "topics_thought": [t["topic"] for t in turns],
            "stop_reason": stop_reason,
            "frontier_growth": frontier_growth,
            "teacher_called": teacher_called,
            "width": max(0.0, min(1.0, float(width))),
            "recovered_total": sorted(recovered_total)}

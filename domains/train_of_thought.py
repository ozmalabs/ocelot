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
#  ATTENTION-WIDTH — the transition-breadth axis, QUANTIZED (DISCRETE QUANTA).
#
#  ONTOLOGY (the substrate's premise, corrected): breadth is NOT a float on a
#  continuum, and NOT a coarse hardcoded int — it is DISCRETE QUANTA. The width is
#  k quanta of breadth at a CONFIGURABLE grain: width = k * grain (integer k). The
#  grain is the RESOLUTION dial — make it finer to get more breadth levels, never
#  by reaching for a raw float. A caller-supplied width is SNAPPED the substrate's
#  native way — k = round(width / grain) (exactly analogy_search._round_to_vocab /
#  observer_aperture grain: value snapped onto k * quantum) — then clamped to the
#  structurally meaningful shell count. So the axis is INTEGER quanta of breadth,
#  and every float that ever appears is only an INPUT that gets snapped on entry.
#
#  This is the GRAPH-WALK ANALOGUE of aperture, and a DISTINCT axis from it: the
#  substrate's `aperture` (observer_aperture resolves/grain) governs the RESOLUTION
#  of a readout over a signature FIELD; attention_width governs the BREADTH of the
#  neighbourhood a train of thought admits as its next transitions over the concept
#  GRAPH. Both are a narrow<->wide dial quantized onto k * quantum, but they live
#  in different spaces — so this is named distinctly and does NOT touch
#  resolves/grain.
#
#  What the quanta LAND ON structurally are NEIGHBOURHOOD SHELLS (Christoff et al.'s
#  deliberate<->associative continuum, now as integer shells k):
#    k = 0  narrow / GOAL-DIRECTED  — residual + is-a ancestors only (the
#           deliberately-constrained regime; == residual_stance, the default);
#    k = 1  +1 shell — add is-a CHILDREN (in_neighbours) + SIBLINGS (co-children);
#    k = 2  +2 shell / wide / ASSOCIATIVE — add the full associative neighbours over
#           analogy_search._DEFAULT_REL_EDGES (spreading activation), James's
#           transitive/associative flights.
#  'Could it be both?' — yes: goal-directed and associative are the two ENDS of one
#  adjustable axis (k=0 .. k=WIDTH_MAX_SHELL), not two stances.
#
#  DEFAULT GRAIN preserves block 347's demonstrated shapes: at grain 0.5 the
#  exercised widths snap width 0.0 -> k=0, width 0.5 -> k=1, width 1.0 -> k=2,
#  reproducing the goal / children+siblings / associative trains exactly.
# --------------------------------------------------------------------------- #
#: the configurable QUANTUM GRAIN of the breadth axis. Resolution = fineness of
#: the quantum: a finer grain yields more integer breadth levels between the
#: shells; the DEFAULT 0.5 snaps 347's demonstrated widths (0.0/0.5/1.0) onto the
#: shell indices 0/1/2 so those train shapes reproduce.
WIDTH_QUANTUM: float = 0.5
#: the number of structural neighbourhood SHELLS the quanta land on (k is clamped
#: here): 0 = goal core, 1 = +children/siblings, 2 = +associative neighbours.
WIDTH_MAX_SHELL: int = 2


def snap_width_to_quanta(width, quantum: float = WIDTH_QUANTUM,
                         max_shell: int = WIDTH_MAX_SHELL) -> int:
    """Snap a breadth `width` onto its DISCRETE QUANTUM — the integer shell count
    k = round(width / quantum), clamped to [0, max_shell]. This is the substrate's
    native quantiser (analogy_search._round_to_vocab / observer_aperture grain:
    value -> k * quantum), applied to the breadth axis. `width` may arrive as a
    float (a caller convenience / a legacy 347 value) OR already as an integer
    number of quanta; either way it is snapped to the canonical integer k. Passing
    a raw float never leaks a continuum in — it is resolved to a quantum on entry.
    Resolution is set by `quantum` (finer = more levels), never by a raw float."""
    try:
        k = round(float(width) / float(quantum))
    except Exception:
        k = 0
    return max(0, min(int(max_shell), int(k)))
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


def breadth_stance(width, quantum: float = WIDTH_QUANTUM,
                   max_shell: int = WIDTH_MAX_SHELL) -> Callable[[Any, dict, set], list[str]]:
    """A graded stance at attention-width `width`, expressed as DISCRETE QUANTA.
    `width` is snapped to an integer shell count k = round(width/quantum) (clamped
    to [0, max_shell]) — the substrate's native quantiser. k = 0 is byte-for-byte
    the goal-directed residual_stance; each +1 quantum widens the admitted
    transition neighbourhood by one structural SHELL (k=1 adds children + siblings,
    k=2 adds the full associative relation-neighbours). The next topics are ordered
    goal-first so a mid-breadth train stays anchored while it also wanders."""
    k = snap_width_to_quanta(width, quantum, max_shell)

    def _stance(wa, turn: dict, seen: set) -> list[str]:
        topic = turn.get("topic", "")
        nxt: list[str] = []

        def _add(items):
            for c in items:
                if c and c not in seen and c != topic and c not in nxt:
                    nxt.append(c)

        # shell 0 (k>=0) always includes the goal-directed core (residual + ancestors)
        _add(c for c in (turn.get("residual") or []))
        _add(transitive_ancestors(wa, topic))
        if k <= 0:
            return nxt

        sub = sd._sub(wa)
        node = sd._find_concept(sub, topic)
        if node is None:
            return nxt
        # +1 shell: lateral/downward associative steps (children + siblings)
        if k >= 1:
            _add(_children(sub, node))
            _add(_siblings(sub, node, topic))
        # +2 shell: full associative spreading over the relation edge-classes
        if k >= 2:
            _add(_relation_neighbours(sub, node, topic))
        return nxt

    return _stance


# convenience named points on the axis (still one axis — these are just integer
# quanta of breadth: shell 0 and the widest shell)
def goal_stance(wa, turn, seen):        # k = 0 quanta
    return breadth_stance(0)(wa, turn, seen)


def associative_stance(wa, turn, seen):  # k = WIDTH_MAX_SHELL quanta
    return breadth_stance(WIDTH_MAX_SHELL * WIDTH_QUANTUM)(wa, turn, seen)


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
                           width=0,
                           novelty_window: Optional[int] = 3,
                           on_unknown: str = "return",
                           ask_fn: Optional[Callable[[str], Any]] = None,
                           enqueue: bool = True) -> dict[str, Any]:
    """Run the inner unspoken conversation: pick a starting topic (given or from a
    filed knowledge SelfConcern), then chain covert turns — each turn's next topics
    chosen by the STANCE over (turn, seen).

    ATTENTION-WIDTH: `width` sets the transition breadth on the goal<->associative
    axis, expressed as DISCRETE QUANTA (shells). It is snapped to an integer shell
    count k = round(width/WIDTH_QUANTUM) (0 = goal-directed / is-a spine, up to
    WIDTH_MAX_SHELL = wide associative) via breadth_stance. It is used when neither
    `stance` nor `stance_fn` is given (the honest default k=0 == the block-346
    residual_stance, backward-compatible). `width` may be an integer number of
    quanta OR a legacy float value — either is snapped on entry (a raw float never
    leaks a continuum in). An explicit `stance` name or `stance_fn` overrides the
    width axis.

    HONEST TERMINATION (a dynamic on the axis, not a bolted-on rule): the train
    disengages when the last `novelty_window` turns recovered NOTHING new (novelty
    stalled) — the anti-rumination stop (a train circling without learning lets go),
    stop_reason='novelty_stalled'. Set novelty_window=None to disable (pure agenda-
    exhaustion, the block-346 behavior). [Richer upgrade, noted: drive this from the
    learning_progress_curiosity smoothed_progress signal instead of the novelty
    proxy.]

    Returns {turns, topics_thought, stop_reason, frontier_growth, teacher_called,
    width, width_quanta, recovered_total}. `width_quanta` is the snapped integer
    shell count k actually used; `width` echoes it (integer quanta, not a float)."""
    if stance_fn is None:
        stance_fn = _STANCES.get(stance) if stance else None
    width_quanta = snap_width_to_quanta(width)
    if stance_fn is None:
        stance_fn = breadth_stance(width)      # the quantized width axis (k=0 == residual_stance)
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
            "width": width_quanta,
            "width_quanta": width_quanta,
            "recovered_total": sorted(recovered_total)}

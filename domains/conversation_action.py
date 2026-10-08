"""conversation_action — HOST WIRING that turns comprehend_text's derived intent
into an ACT (mint a Goal + fire the agent's OWN faculty) or an ASK-BACK (a repair
first-pair-part about a comprehension gap), so the live converse loop no longer
just answers-or-acknowledges.

CLAUDE.md discipline: NO agent decision lives here. This module is the mechanical
translator between `comprehend_text.Comprehension` (the general front end, read
only) and the agent's held machinery:

  • ACT — `act_on_instruction`: mint a Goal node (graph-resident record that the
    instruction became a goal — the "action happened" evidence), then route to a
    HELD faculty by a small keyword registry (the same style as
    `world_adapter._QUESTION_LEADS` / `_IMPERATIVE_LEADS`, surface cues only):
      - a SELF-REPORT predicate about the self (describe/tell/report … your
        organisation / yourself / shape) → `reflective_faculty.reflect` over the
        real self-state → `world_adapter._surface_self_state` → PRODUCED prose
        (the agent's own production faculty; donkey=0);
      - a DESCRIBE predicate over an ATTACHED scene → the SELF-BUILT describe
        faculty (the agent's OWN authored comprehend_describe + communicate rules,
        `scripts/arc_self_report`) mints the describe-Goal and a produce-utterance
        subgoal per percept → the agent SELF-REPORTS via its language faculty;
      - anything else (a nav/manipulation predicate with no world, or a general
        predicate) → mint the Goal and report HONESTLY what it can/can't do — it
        does NOT fake an action it has no faculty/world for.

  • ASK-BACK — `ask_back`: a comprehension GAP (an untyped, by-position head the
    agent could not even POS-type, or an honest `path=="frontier"` dispatch) is
    turned into a repair FIRST-PAIR-PART: an outbound Message with a
    `clarification` speech act (the conversation seed's adjacency-pair vocabulary),
    `responds_to` the inbound, `expects_response`. The trouble source is the
    user's OWN word quoted back verbatim (other-initiated repair) — never a
    fabricated answer, never synthesized content for a by-position gap.

The CONTENT is always the agent's real graph state / produced speech; the WORDS
are the production grammar's or (for the repair template) an honest host template
quoting the real trouble source. WHICH faculty a predicate routes to is a
mechanical registry, not a decision over graph state.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import reflective_faculty as _rf


def realize_frame_reply(agent, frame: dict, audience_snap=None, *, language="en"):
    """Mechanical bridge to the world adapter's active frame producer."""
    return agent._realize_frame_reply(frame, audience_snap, language=language)


def floor_holding_reply(register: str = "neutral") -> str:
    """Return a short register-shaped floor holder for a deep turn."""
    return {"formal": "Let me consider how that connects.",
            "casual": "Let me see how that connects.",
            "neutral": "Looking at how that connects."}.get(
                str(register), "Looking at how that connects.")


# --- SMOOTHING (mechanical connective-join over the agent's OWN produced pieces)
#
# The agent's substantive replies come out as one produced sentence PER item (a
# percept, a capability frame): "The grey thing stays. The yellow counter. The
# blue thing moves." That is choppy, not fluent. Smoothing is admissible world-
# adapter I/O: it JOINS the agent's own already-produced clauses with connectives
# (commas + a trailing "and") and an optional lead-in — it authors NO new content,
# only glue (the same class as the register-surface lead-ins the agent already
# uses). Register shapes the framing: formal -> an elaborated lead / restated
# subject; casual -> bare and terse; neutral -> a plain lead. Same content, register-
# shaped delivery — aligned with the terse-vs-explicit spectrum
# domains/audience_driven_production.py selects over (consumed read-only in spirit:
# richer/formal audience -> more elaborated, casual -> terser).

def _oxford(items: list[str]) -> str:
    """Join clauses with commas + a trailing 'and' (Oxford comma for 3+). Pure glue."""
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _declause(sentence: str) -> str:
    """Strip terminal sentence punctuation from a produced clause (mechanical)."""
    return (sentence or "").strip().rstrip(".!?").strip()


def _lower_article(core: str) -> str:
    """Lower-case a leading article so a clause reads mid-sentence ('The X' -> 'the X').
    Only touches a leading article — never mutates content words."""
    for art in ("The ", "A ", "An "):
        if core.startswith(art):
            return core[0].lower() + core[1:]
    return core


def _oxford_with_connectives(items: list[str], connectives: Optional[list] = None) -> str:
    """GENERALISED `_oxford`: join ``items`` with a comma, using the
    RELATION-APPROPRIATE connective at a juncture where ``connectives[i]``
    (the join BEFORE ``items[i]``) is set, and falling back to the plain
    Oxford "and" convention (intermediate junctures get a bare comma, the
    FINAL juncture gets ", and " / " and ") everywhere else — i.e. this is
    `_oxford` itself when every entry of ``connectives`` is falsy (proof:
    with `conn` always None the branch below always takes the `elif`/`else`
    arms, reproducing `_oxford`'s own join exactly). The connective WORD is
    never chosen here — it is read from whatever the caller already decided
    (a held graph rule's output, or nothing); this only glues."""
    n = len(items)
    if n == 0:
        return ""
    if n == 1:
        return items[0]
    conns = list(connectives) if connectives is not None else [None] * n
    out = items[0]
    for i in range(1, n):
        conn = conns[i] if i < len(conns) else None
        if conn:
            out += ", " + conn + " " + items[i]
        elif i == n - 1:
            out += (", and " if n >= 3 else " and ") + items[i]
        else:
            out += ", " + items[i]
    return out


def smooth_scene_prose(clauses: list[str], register: str = "neutral",
                       connectives: Optional[list] = None,
                       elide_leading: Optional[list] = None,
                       elide_trailing: Optional[list] = None) -> str:
    """Join per-percept produced sentences into ONE connected sentence. Register:
    formal -> elaborated lead ('I observe ...'); casual -> bare (terser, no lead);
    neutral -> plain lead ('I see ...'). Oxford-joined by default; a single clause
    is returned verbatim (with a lead for non-casual). Mechanical — the clauses
    are the agent's own.

    THREE OPTIONAL fluency parameters, each a list PARALLEL to ``clauses``
    (index i describes clause i), read from held graph decisions upstream
    (e.g. domains.recount_faculty.recount_report reading seeds/recount_
    fluency.json's rule output) — this function makes NO decision about
    which relation gets which connective or which mention is a repeat; it
    only reads the caller's answer and performs the mechanical surgery:
      * ``connectives[i]``: the connective word to join clause i-1 -> clause i
        with (e.g. "then"), instead of the plain Oxford default ("and"/comma).
      * ``elide_leading[i]``: how many LEADING words of clause i's own
        ALREADY-PRODUCED text to drop (a repeated subject NP) — never applied
        to clause 0 (there is no antecedent to elide against).
      * ``elide_trailing[i]``: an optional (n_words, pronoun) pair — drop the
        LAST n_words of clause i's text and splice in ``pronoun`` (a repeated
        object NP -> a pronoun).
    All three default to None, in which case this function's output is BYTE-
    IDENTICAL to its pre-fluency behaviour (see `_oxford_with_connectives`'s
    own equivalence note; the elision/pronoun steps are no-ops when their
    list is absent). Existing callers (scripts/arc_self_report.py,
    domains/conversation_action._act_describe_scene) pass none of these and
    are therefore unaffected."""
    kept = [(i, c) for i, c in enumerate(clauses) if _declause(c)]
    if not kept:
        return ""
    n = len(clauses)
    conns = list(connectives) if connectives is not None else [None] * n
    leads = list(elide_leading) if elide_leading is not None else [0] * n
    trails = list(elide_trailing) if elide_trailing is not None else [None] * n
    pieces: list[str] = []
    piece_conns: list = []
    for pos, (i, raw) in enumerate(kept):
        words = _declause(raw).split(" ")
        k = leads[i] if i < len(leads) else 0
        elided = bool(pos > 0 and k and k < len(words))
        if elided:
            # a repeated subject NP the agent's OWN rule flagged — drop the
            # LEADING words `prod.produce` actually used for that role's NP
            # (see recount_faculty._np_word_count_from_production); the
            # remaining words were never sentence-initial in the original
            # produced clause, so they are already correctly cased.
            words = words[k:]
        else:
            core2 = " ".join(words)
            if not (pos == 0 and register == "casual"):
                core2 = _lower_article(core2)
            words = core2.split(" ")
        pron = trails[i] if i < len(trails) else None
        if pron:
            drop_n, pronoun = pron
            if drop_n and 0 < drop_n < len(words):
                # a repeated object NP the agent's OWN rule flagged — drop
                # the TRAILING words that NP used and splice in the held
                # pronoun surface (also a grounded LexEntry — see
                # recount_faculty.project_read_scene's RecountVocabulary
                # bridging — even though the splice itself is glue, not a
                # fresh `prod.produce` call: the pronoun WORD is held data,
                # never a Python literal choosing it).
                words = words[:-drop_n] + [pronoun]
        pieces.append(" ".join(words))
        piece_conns.append(conns[i] if i < len(conns) else None)
    body = _oxford_with_connectives(pieces, piece_conns)
    if register == "casual":
        return body + "."
    lead = "I observe" if register == "formal" else "I see"
    return lead + " " + body + "."


def smooth_first_person(clauses: list[str], register: str = "neutral") -> str:
    """Join first-person produced clauses ('I modify the rule.', 'I hold the rule.')
    into ONE connected sentence. A single clause is returned verbatim. When every
    clause shares the 'I ' subject: casual/neutral collapse it once and Oxford-join the
    predicates ('I modify the rule, hold the rule, and hold the term.'); formal restates
    the subject per predicate, connected with semicolons ('I modify the rule; I hold the
    rule; ...') — more elaborated, still one flowing sentence. Mechanical join."""
    cores = [_declause(c) for c in clauses if _declause(c)]
    if not cores:
        return ""
    if len(cores) == 1:
        return cores[0] + "."
    if all(c.startswith("I ") for c in cores):
        preds = [c[len("I "):] for c in cores]
        if register == "formal":
            return "; ".join("I " + p for p in preds) + "."
        return "I " + _oxford(preds) + "."
    return _oxford(cores) + "."


# --- registries (surface cues only — the I/O-boundary style) -----------------

# predicates whose imperative use is a request to PRODUCE an account
_SELF_REPORT_VERBS = frozenset({
    "describe", "tell", "report", "explain", "say", "show", "state", "list",
    "account", "summarise", "summarize",
})

# predicates whose imperative use FRAMES A CONCERN — a discrimination / attention /
# self-correction STRATEGY the agent should take on AS ITS OWN (not a here-and-now
# world action). Routed to the held `induce_concern`/`ground_concern` loop: the agent
# forms the concern from the directive's OWN structure (author_signature over the held
# RelationCue lexicon) and grounds it, teacher-free. Surface cues only — the same
# registry style as _SELF_REPORT_VERBS / world_adapter._IMPERATIVE_LEADS. Overlap with
# _SELF_REPORT_VERBS is harmless: the self-report branch is checked first and returns.
_CONCERN_FRAMING_VERBS = frozenset({
    "hold", "compare", "contrast", "distinguish", "differentiate", "discriminate",
    "separate", "notice", "attend", "weigh", "judge", "decide", "learn", "focus",
})

# a self-referential topic keyword -> the held reflective faculty that answers it.
# every value is a key in reflective_faculty._DISPATCH (a real, read-only graph query).
_SELF_TARGET_KW = (
    ("organis", "self_organisation"), ("organiz", "self_organisation"),
    ("shape", "self_shape"),
    ("yourself", "self_identity"), ("identity", "self_identity"),
    ("who you are", "self_identity"), ("about you", "self_identity"),
    ("limit", "frontier"), ("frontier", "frontier"),
    ("modif", "self_modification"),
)

_SELF_WORDS = frozenset({"yourself", "you", "your", "me", "myself", "self"})

# a perception complement -> this is a describe-the-SCENE instruction, not a
# self-report, even though the embedded 'you' ('describe what YOU see') is a
# generic self-reference.
_PERCEPTION_CUES = frozenset({"see", "seeing", "look", "looking", "around",
                              "there", "scene", "perceive", "observe", "view",
                              "front", "watch"})


def _self_target_strong(text: str) -> Optional[str]:
    """A SPECIFIC self-topic keyword (organisation / shape / yourself / …) -> its
    held reflective faculty. Keyword table only; no generic-pronoun fallback."""
    low = (text or "").lower()
    for kw, tgt in _SELF_TARGET_KW:
        if kw in low:
            return tgt
    return None


def _words(text: str) -> list[str]:
    return [w.strip(",.;:?!\"'()") for w in (text or "").lower().split()]


def _has_generic_self_ref(text: str) -> bool:
    return any(w in _SELF_WORDS for w in _words(text))


def _has_perception_cue(text: str) -> bool:
    return any(w in _PERCEPTION_CUES for w in _words(text))


# --- Goal minting (mechanical graph ingest — the "action happened" record) ----

def _bind_goal_to_inbound(agent, goal, inbound=None) -> Any:
    """Mechanically bind a conversation goal to its source Message.

    The edge and origin field are provenance only; this helper does not select
    an outcome.  The edge check keeps repeated wiring idempotent, while
    ``inbound=None`` preserves callers that mint goals outside a live message.
    """
    if inbound is None or goal is None:
        return goal
    try:
        if not agent.s.has_node(goal) or not agent.s.has_node(inbound):
            return goal
        if not agent.inner.has_edge(goal, "comprehends", inbound):
            agent.inner.add_edge_unchecked(goal, "comprehends", inbound)
        if agent.s.node(goal)["attrs"].get("origin_turn_id") is None:
            agent.inner.set_attr(goal, "origin_turn_id", int(inbound.value))
    except Exception:
        # Provenance must not change the existing action bridge's compatibility
        # behavior when a host supplies an object outside the graph.
        pass
    return goal


def _mint_goal(agent, kind: str, predicate, obj, inbound=None, **extra) -> Any:
    """Mint a Goal node from the comprehended instruction and hub it to the agent
    (`has_goal`), exactly as the question driver / world_receive ingest goals.
    Mechanical translation of comprehend_text's intent into a graph node — no
    decision. Returns the Goal id.  If ``inbound`` is supplied, the goal is
    idempotently linked to that Message and records ``origin_turn_id``."""
    attrs = {"kind": kind, "predicate": predicate or "", "object": obj or "",
             "source": "conversation"}
    attrs.update({k: v for k, v in extra.items() if v is not None})
    g = agent.s.add_node("Goal", attrs)
    try:
        agent.s.add_edge(agent.agent, "has_goal", g)
    except Exception:
        agent.inner.add_edge_unchecked(agent.agent, "has_goal", g)
    _bind_goal_to_inbound(agent, g, inbound)
    from domains import interlocutor_model as _im
    _im.wanted_by(agent, g)
    return g


def _record_live_goal_event(agent, inbound, goal, kind, *, payload=None):
    """Record a lifecycle event on the inbound Goal's discourse state.

    This is mechanical provenance around the selected self-report faculty.
    The goal ID is passed directly; it is never reconstructed from event order
    or recipient. Native rules apply the lifecycle transition.
    """
    if inbound is None or goal is None or not agent.s.has_node(inbound):
        return None
    attrs = agent.s.node(inbound)["attrs"]
    state = attrs.get("discourse_state_id")
    origin = attrs.get("discourse_event_id")
    if (state is None or origin is None or not agent.s.has_node(state)
            or not agent.s.has_node(origin) or not agent.s.has_node(goal)):
        return None
    from domains.discourse_state import record_event
    ga = agent.s.node(goal)["attrs"]
    if ga.get("lifecycle_status") is None:
        agent.inner.set_attr(goal, "lifecycle_status", "proposed")
        if ga.get("status") is None:
            agent.inner.set_attr(goal, "status", "proposed")
    if goal not in agent.inner.neighbours(state, "has_active_goal"):
        agent.inner.add_edge_unchecked(state, "has_active_goal", goal)
    if origin not in agent.inner.neighbours(goal, "originated_in"):
        agent.inner.add_edge_unchecked(goal, "originated_in", origin)
    if inbound not in agent.inner.neighbours(goal, "comprehends"):
        agent.inner.add_edge_unchecked(goal, "comprehends", inbound)
    speakers = list(agent.inner.neighbours(inbound, "sent_by"))
    event = record_event(agent, state, kind=kind, speaker=agent.agent,
        addressee=speakers[0] if speakers else None,
        interaction_mode="event", payload=payload, goal=goal)
    agent.inner.run_rules()
    return event


# --- describe-scene faculty (the agent's OWN authored rules; donkey=0) --------

def attach_scene(agent, percepts: list[dict]) -> Any:
    """WORLD ADAPTER helper: give the conversing agent a perceivable Scene (a list
    of percept attr-dicts, shaped like the live eye's Features: kind + colour …).
    Mints Scene + Percept nodes and stores the scene on the agent so a subsequent
    'describe what you see' instruction can be ACTED on. Mechanical ingest."""
    scene = agent.s.add_node("Scene", {})
    for ctx in percepts:
        agent.inner.add_edge_unchecked(scene, "has_percept", agent.s.add_node("Percept", dict(ctx)))
    agent._conv_scene = scene
    native_steps = agent.inner.run_rules()
    # The scene is materialized by the native rule engine.  Keep this receipt
    # separate from any later describe/communicate outcome: this host helper
    # only ingests percepts and reads the native materialization boundary back.
    receipt = agent.s.add_node("NativeSceneMaterializationReceipt", {
        "schema": "native_scene_materialization_receipt.v1",
        "cluster": "conversation_action.scene_materialization",
        "provenance": "native_rule_readback:scene_percept_materialization",
        "native_rule": "conversation_action_scene_percept_materialization_v1",
        "scene": scene,
        "percept_count": len(percepts),
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "has_native_scene_materialization_receipt", receipt)
    return scene


def _ensure_describe(agent):
    """Lazily build (once, cached) the agent's SELF-BUILT describe faculty + its
    production voice, reusing the proven `scripts/arc_self_report` machinery: the
    agent AUTHORS its comprehend_describe + communicate rules from framed concerns
    (via the composer, donkey=0); the LanguageProduction is its voice. Returns the
    prod, or None if the language stack is unavailable."""
    cached = getattr(agent, "_conv_describe", None)
    if cached is not None:
        return cached or None
    try:
        import scripts.arc_self_report as _asr
        from domains.language_world import LanguageWorld, teacher_stub
        from domains.language_production import LanguageProduction
        from scripts.language_test import training_bank
        _asr.build_describe_faculty(agent)
        world = LanguageWorld(agent.inner, training_bank(), teacher_stub)
        world.run()
        world.teacher_disabled = True
        prod = LanguageProduction(world)
        agent._conv_describe = (prod, _asr)
    except Exception:
        agent._conv_describe = False
        return None
    return agent._conv_describe


# frame words that carry no percept identity — skip them when picking a per-line
# token so the token lands on the distinctive word (a colour / kind word).
_LINE_STOP = frozenset({"the", "and", "thing", "that", "this", "there", "here",
                        "its", "are", "was", "see", "observe", "with", "has"})


def _conceptualize_scene_lines(agent, lines):
    """Route the produced per-percept LINES through the conceptualizer (form INTENT -> shape by
    residual-vs-THIS-interlocutor -> monitor -> commit) so the describe reply is AUDIENCE-
    DESIGNED: a GROUNDED audience (credited with some percepts) commits a terser conveyed
    subset; an UNGROUNDED/unknown one commits the explicit full set. Builds a comprehend-safe
    single-word token per line (its first distinctive word, else a positional token), forms the
    intent over those tokens, and maps the committed CONVEYED tokens back to their lines (order
    preserved). The host makes NO shape decision — WHICH tokens are conveyed is READ OFF the
    committed utterance the jabberwock's rules produced. Returns (delivered_lines, result); on
    any failure returns (lines, None) — the honest full-prose fallback."""
    import re
    if not lines:
        return [], None
    try:
        from domains import conceptualizer as _cc
        used, tokens = set(), []
        for i, ln in enumerate(lines):
            words = [w for w in re.findall(r"[a-z]+", ln.lower()) if len(w) >= 3]
            cand = next((w for w in words if w not in used and w not in _LINE_STOP), None)
            tok = cand or f"item{i}"
            used.add(tok)
            tokens.append(tok)
        lexicon = [{"form": t, "concept": t} for t in tokens]
        interlocutor = agent._interlocutor_snapshot()
        # the accumulated audience may credit concepts beyond this reply's tokens (its common
        # ground); ensure each credited-known concept stays renderable (mechanical self-surfaces).
        lexicon = agent._lexicon_with_known(lexicon, interlocutor)
        result = _cc.conceptualize_reply(agent, "inform", tokens, interlocutor, lexicon, rounds=4)
        agent._last_reply_intent = result
        committed = result["committed"]["utterance"]
        if committed is None:
            return lines, None
        conveyed = set(str(committed).split())
        delivered = [ln for tok, ln in zip(tokens, lines) if tok in conveyed]
        return (delivered or lines), result
    except Exception:
        return lines, None


def _act_describe_scene(agent, comp, inbound) -> dict:
    """ACT on a 'describe what you see' over the ATTACHED scene: the WORLD receives
    the instruction as a Message the agent perceives; the agent's OWN authored
    rules mint the describe-Goal + a produce-utterance subgoal per percept; the
    jabberwock SELF-REPORTS via its language faculty. The host only reads the
    produced lines back. served_by = the agent's authored rules.

    PHASE 3 — the concept-level content path routes through the CONCEPTUALIZER: the
    produced lines FORM a communicative intent, are SHAPED for THIS interlocutor
    (audience-designed: a grounded audience commits a terser conveyed subset, an
    ungrounded one the explicit full set), and are MONITOR-gated before delivery.
    The committed conveyed lines are then SMOOTHED into fluent prose — fluency kept,
    delivery audience-designed."""
    built = _ensure_describe(agent)
    scene = getattr(agent, "_conv_scene", None)
    if not built or scene is None:
        return {"acted": False, "reply": None, "route": "describe_scene",
                "note": "no scene attached / language stack unavailable"}
    prod, asr = built
    before_goals = {int(g.value if hasattr(g, "value") else g)
                    for g in agent.s.nodes("Goal")}
    request_scene = asr.request_scene_view(agent, scene)
    request_message = asr.world_receive(agent, request_scene, comp.raw, message=inbound)
    agent.inner.run_rules()
    # Bind only the Goal newly minted by the authored rule for this request
    # message. A global last-Goal scan can silently reuse a prior request's
    # parent when a Scene has already been described.
    goals = [g for g in agent.s.nodes("Goal")
             if agent.inner.has_node(g)
             and int(g.value if hasattr(g, "value") else g) not in before_goals
             and agent.s.node(g)["attrs"].get("kind") == "describe_scene"
             and request_message in agent.inner.neighbours(g, "comprehends")]
    goal = goals[0] if len(goals) == 1 else None
    if goal is None:
        return {"acted": False, "reply": None, "route": "describe_scene",
                "goal": None, "goal_kind": "describe_scene",
                "note": f"authored rule produced {len(goals)} request-owned parent Goals; expected exactly one"}
    _bind_goal_to_inbound(agent, goal, inbound)
    lifecycle_payload = {"action_route": "describe_scene",
                         "request_message_id": int(request_message.value if hasattr(request_message, "value") else request_message)}
    _record_live_goal_event(agent, inbound, goal, "selection", payload=lifecycle_payload)
    _record_live_goal_event(agent, inbound, goal, "execution", payload=lifecycle_payload)
    try:
        ng, nsg, lines = asr.self_report(agent, prod, parent_goal=goal)
    except Exception:
        ng, nsg, lines = 1, 0, []
    _record_live_goal_event(agent, inbound, goal,
        "action_result" if lines else "action_failure",
        payload={**lifecycle_payload,
                 "outcome": "faculty_returned" if lines else "faculty_failed_or_empty"})
    # CONCEPTUALIZE: form + shape + monitor + commit -> the audience-designed conveyed
    # subset of lines (mechanical map-back from the committed utterance). Falls back to
    # the full line set on any failure — never silent.
    delivered_lines, intent_result = _conceptualize_scene_lines(agent, lines)
    # SMOOTH: connect the agent's own per-percept produced sentences into one fluent
    # sentence, shaped by the tracked interlocutor register (the SELECTION is the
    # agent's — read off register(); the join is mechanical).
    try:
        reg = agent.register()
    except Exception:
        reg = "neutral"
    reply = smooth_scene_prose(delivered_lines, reg) if delivered_lines else None
    return {"acted": bool(lines), "reply": reply, "route": "describe_scene",
            "conceptualized": intent_result is not None,
            "intent": (intent_result or {}).get("intent"),
            "goal": goal, "goal_kind": "describe_scene",
            "subgoals": nsg, "served_by": "agent_rule:comprehend_describe+communicate",
            "note": f"the agent authored the describe/communicate rules (donkey=0); "
                    f"minted {ng} describe-Goal + {nsg} produce-utterance subgoals; "
                    f"conceptualizer-shaped delivery={intent_result is not None}"}


# --- CONCERN AUTHORING (the NL front-door to the self-authoring loop) ---------

def _act_author_concern(agent, comp, inbound=None) -> dict:
    """A concern-framing INSTRUCTION -> the agent's OWN self-authoring loop.

    THE NATURAL-LANGUAGE FRONT DOOR. Before this wiring, a directive that framed a
    strategy ("hold both open when two come out close; decide where they differ")
    reached `act_on_instruction`'s honest goal-only dead end — the Goal was minted and
    the agent reported it had no faculty to carry it out, even though it HAS the faculty
    to form a concern from it. This routes such a directive into that faculty.

    Mechanical wiring only (CLAUDE.md): (1) ingest the directive's own text as a
    `Concept.definition` (text -> node, adapter I/O); (2) fire the HELD RelationCue
    lexicon over it via `reflective_faculty.author_signature` — keyword-presence is
    perception, the SAME text->structure translation the agent uses to read any
    concept's structure, NOT a decision; (3) hand the earned signature to the agent's
    OWN `induce_concern` (the seeded ShapeDecode dequantize/mint loop) and, when it
    MINTS a genuinely-novel CapabilityAxis, `ground_concern` (the seeded composer
    dispatch). Every DECISION — does a held shape already cover this? what does the
    residual ground to? — is the seeded Rust loop's, read back here into an honest
    reply (including an honest WALL when the residual grounds to no held relation)."""
    text = comp.raw or ""
    stem = "_".join(w for w in _words(text) if w)[:56] or "steer"
    name = "steer_" + stem
    try:
        agent.s.add_node("Concept", {"name": name, "definition": text})
        sig, _defn, _cn = _rf.author_signature(agent.s, name)
    except Exception:
        sig = None
    d = comp.dispatch or {}
    goal = _mint_goal(agent, "author_concern", d.get("predicate"),
                      d.get("object"), inbound=inbound)

    if not sig:
        return {"acted": True, "route": "concern_authored", "goal": goal,
                "goal_kind": "author_concern", "concern": None,
                "served_by": "reflective_faculty:author_signature",
                "reply": "I took that as something to attend to, but my relation lexicon "
                         "grounded none of its structure — I could form no concern from it yet.",
                "note": "author_signature fired no RelationCue over the directive — honest lexicon gap"}

    ind = _rf.induce_concern(agent, sig, name_hint=name)
    minted = bool(ind.get("minted"))
    if minted:
        key = ind.get("capability_key")
        gr = _rf.ground_concern(agent, [key])
        grounded = bool(gr.get("grounded"))
        path = gr.get("form") or gr.get("path") or gr.get("wall")
        if grounded:
            reply = (f"I formed that into a new concern I hold as {key!r}, and grounded it "
                     f"as {gr.get('form') or gr.get('path')} — I can act on it.")
        else:
            reply = (f"I formed that into a new concern I hold as {key!r}, but its residual "
                     f"grounds to no held structure I can act on yet — an honest frontier.")
    else:
        key = ind.get("covered_by")
        grounded, path = False, "covered"
        reply = (f"That already matches a shape I hold ({key!r}); it named no new concern.")

    return {"acted": True, "route": "concern_authored", "goal": goal,
            "goal_kind": "author_concern",
            "served_by": "reflective_faculty:induce_concern+ground_concern",
            "reply": reply,
            "concern": {"key": key, "signature": sig, "minted": minted,
                        "grounded": grounded, "path": path},
            "note": f"authored signature {sig!r}; minted={minted}; grounded={grounded}"}


# --- ACT ---------------------------------------------------------------------

def act_on_instruction(agent, comp, inbound=None) -> dict:
    """Turn a comprehended INSTRUCTION into an ACT. Mints a Goal and routes to a
    held faculty; returns a dict carrying the produced/honest `reply` the converse
    loop speaks. Never fakes an action the agent has no faculty/world for."""
    d = comp.dispatch or {}
    pred = d.get("predicate")
    obj = d.get("object")
    pred_l = (pred or "").lower().strip(",.;:?!")

    # The comprehension faculty has already established that this is a
    # perception request with no attached world.  Preserve that cognition
    # state before generic self-reference handling: the word ``you`` in a
    # perception complement is not evidence for a self-identity report.
    if d.get("path") == "honest_no_world":
        return honest_no_world_reply(agent, comp, inbound)

    scene_attached = getattr(agent, "_conv_scene", None) is not None

    if pred_l in _SELF_REPORT_VERBS:
        strong = _self_target_strong(comp.raw)
        # 2. DESCRIBE the perceived SCENE (perception cue, scene attached) -> the
        #    self-built describe faculty. Checked before the generic self-ref
        #    fallback so 'describe what you see' is perception, not self-report.
        if scene_attached and _has_perception_cue(comp.raw) and not strong:
            out = _act_describe_scene(agent, comp, inbound)
            if out.get("reply") is not None:
                return out
        # 1. SELF-REPORT about the self -> the held reflective faculty -> prose.
        target = strong or ("self_identity" if _has_generic_self_ref(comp.raw) else None)
        if target and target in _rf._DISPATCH:
            # The held reflexive self-report rule already commits a
            # Goal{report_self} to this Message. Adopt that exact graph
            # commitment so the live faculty can attach its event-owned
            # lifecycle instead of minting a parallel Goal. Only reuse a
            # unique event-bound report_self Goal; ambiguous or unrelated
            # state keeps the ordinary mint path.
            graph_goals = ([goal for goal in agent.inner.neighbours(
                agent.agent, "has_goal")
                if agent.s.has_node(goal)
                and agent.s.node(goal)["attrs"].get("kind") == "report_self"
                and inbound is not None
                and inbound in agent.inner.neighbours(goal, "comprehends")]
                if inbound is not None else [])
            if len(graph_goals) == 1:
                goal = graph_goals[0]
                for key, value in (("predicate", pred or ""),
                                   ("object", obj or ""),
                                   ("self_target", target),
                                   ("source", "conversation")):
                    agent.inner.set_attr(goal, key, value)
                _bind_goal_to_inbound(agent, goal, inbound)
                from domains import interlocutor_model as _im
                _im.wanted_by(agent, goal)
            else:
                goal = _mint_goal(agent, "report_self", pred, obj,
                                  inbound=inbound, self_target=target)
            lifecycle_payload = {"action_route": "self_report",
                                 "faculty_target": target,
                                 "predicate": pred or ""}
            _record_live_goal_event(agent, inbound, goal, "selection",
                                    payload=lifecycle_payload)
            _record_live_goal_event(agent, inbound, goal, "execution",
                                    payload=lifecycle_payload)
            try:
                state = _rf.reflect(target, None, agent.s)
                reply = agent._surface_self_state(state)
            except Exception:
                reply = None
            _record_live_goal_event(agent, inbound, goal,
                "action_result" if reply else "action_failure",
                payload={**lifecycle_payload,
                         "outcome": "faculty_returned" if reply else "faculty_failed_or_empty"})
            return {"acted": reply is not None, "reply": reply, "route": "self_report",
                    "goal": goal, "goal_kind": "report_self",
                    "served_by": f"self_model:{target}",
                    "note": "minted a report_self Goal; content is my real self-state, "
                            "rendered through my production faculty (donkey=0)"}

        # a describe/report with no self-topic but a scene attached -> describe it.
        if scene_attached:
            out = _act_describe_scene(agent, comp, inbound)
            if out.get("reply") is not None:
                return out

    # 2.5 A CONCERN-FRAMING instruction (a discrimination / attention / self-correction
    #     STRATEGY to take on) -> the agent's OWN self-authoring loop (induce_concern /
    #     ground_concern). Checked before the honest goal-only give-up: a directive like
    #     "hold both candidates open when two come out close and decide where they differ"
    #     is not an action the agent has no world for — it is a concern the agent can FORM.
    if pred_l in _CONCERN_FRAMING_VERBS or any(w in _CONCERN_FRAMING_VERBS for w in _words(comp.raw)):
        out = _act_author_concern(agent, comp, inbound)
        if out.get("reply") is not None:
            return out

    action_evidence = d.get("language_evidence") or {}
    if action_evidence.get("anaphoric_reference") \
            and action_evidence.get("referent_status") == "unresolved":
        # An unresolved typed reference is a cognition/grounding repair, not
        # an action with a guessed object.  Reuse the existing clarification
        # faculty; no surface fallback or lexical target substitution occurs.
        return ask_back(agent, comp, inbound)
    # 3. A perception/nav/manipulation predicate with no attached world, or a
    #    general predicate: mint the Goal, report HONESTLY — no faked action.
    goal = _mint_goal(agent, "instruction", pred, obj, inbound=inbound)
    deferred_condition = action_evidence.get("deferred_condition")
    if deferred_condition and goal is not None:
        # A typed condition changes lifecycle state; it does not authorize an
        # immediate world action. Preserve the evidence on the graph-resident
        # Goal so later cognition can resume it when the condition is observed.
        try:
            agent.inner.set_attr(goal, "status", "deferred")
            agent.inner.set_attr(goal, "defer_reason",
                                 str(action_evidence.get("condition_evidence")
                                     or "typed_condition"))
            agent.inner.set_attr(goal, "action_sequence",
                                 list(action_evidence.get("action_sequence") or
                                      [pred] if pred else []))
        except Exception:
            pass
    has_world = getattr(agent, "_conv_scene", None) is not None
    if deferred_condition:
        target = f" the {obj}" if obj else ""
        note = f'The request to {pred}{target} is deferred.'
        if not has_world:
            note += " I have no attached world/faculty to carry it out here."
    elif pred_l in _SELF_REPORT_VERBS and not has_world:
        note = (f'I took on the goal to {pred}'
                + (f' the {obj}' if obj else '')
                + ", but I have no scene attached to perceive right now.")
    else:
        note = (f'I took on the goal to {pred}'
                + (f' the {obj}' if obj else '')
                + ", but I have no attached world/faculty to carry it out here.")
    return {"acted": True, "reply": note, "route": "goal_only", "goal": goal,
            "goal_kind": "instruction", "served_by": "host_wiring",
            "note": "minted the Goal; honest action-space limit (no faculty/world attached)"}


# --- ASK-BACK ----------------------------------------------------------------

def _head_untyped_gap(comp) -> Optional[str]:
    """The LEADING content token the agent could not even POS-type (role 'gap',
    pos 'by-position') — the strongest 'I do not understand this' signal, and the
    honest trouble source to repair on. Returns its surface, or None."""
    frame = comp.frame or {}
    els = frame.get("elements") or []
    if els and els[0].get("role") == "gap" and els[0].get("pos") == "by-position":
        return els[0].get("surface")
    return None


def _first_untyped_surface(comp) -> Optional[str]:
    for g in comp.gaps or []:
        if g.get("pos") == "by-position" and (g.get("surface") or "").strip():
            return g["surface"]
    return None


def is_ask_back(comp) -> bool:
    """A comprehension GAP the agent should ASK about rather than acknowledge: an
    untyped by-position HEAD (it could not parse the utterance's head at all), or
    an honest `path=='frontier'` dispatch. A question that DID resolve to a
    faculty (meta/know/table) is NOT an ask-back — it answers."""
    if comp is None:
        return False
    d = comp.dispatch or {}
    evidence = d.get("language_evidence") or {}
    if comp.fastpath:
        return False
    if evidence.get("repair_evidence") in {
            "unresolved_selection", "knowledge_deficit",
    }:
        return True
    head_untyped = _head_untyped_gap(comp) is not None
    if comp.kind == "question":
        # only ask back a question that is itself an honest frontier with an
        # untyped head; a resolvable self/world question answers as before.
        return d.get("path") == "frontier" and head_untyped
    return d.get("path") == "frontier" or head_untyped


def ask_back(agent, comp, inbound=None, *, focus_override=None,
             surface_kind_override=None) -> dict:
    """Produce a repair FIRST-PAIR-PART about the gap focus: an outbound Message
    with a `clarification` speech act (adjacency-pair vocabulary from the
    conversation seed), threaded `responds_to` the inbound, `expects_response`.
    The trouble source is the user's OWN word quoted back — other-initiated
    repair, never a fabricated answer. Returns the asked question as `reply`."""
    evidence = (comp.dispatch or {}).get("language_evidence") or {}
    inbound_attrs = (agent.s.node(inbound)["attrs"]
                     if inbound is not None and agent.s.has_node(inbound) else {})
    unresolved_question_reference = (
        comp.kind == "question" and inbound_attrs.get("comp_anaphor"))
    focus = (focus_override or evidence.get("repair_focus") or _head_untyped_gap(comp)
             or _first_untyped_surface(comp)
             or comp.focus or (comp.dispatch or {}).get("reason") or comp.raw)
    surface_kind = surface_kind_override or "inquire_unknown"
    if (surface_kind_override is None
            and evidence.get("repair_evidence") == "nonunderstanding_report"):
        focus = focus_override or evidence.get("repair_focus") or "understanding"
        surface_kind = "inquire_clarification"
    if unresolved_question_reference and surface_kind_override is None:
        # A typed topic with an unresolved discourse referent is not an
        # unknown word. Ask which entity the interlocutor means, using the
        # adapter's selected topic label rather than the wh-relation focus.
        focus = ((comp.dispatch or {}).get("concept")
                 or evidence.get("referent_target") or focus)
        surface_kind = "inquire_reference"
    focus = str(focus).strip(",.;:?!") or comp.raw
    # Render the repair in the interlocutor's REGISTER (the agent's voice): the
    # held `inquire_unknown` surface quotes the real trouble source and matches
    # the register (casual "what's 'X'?" / formal "might I ask what it means?").
    # Fall back to the plain honest template if the register lexicon is absent.
    surface = None
    try:
        surface = agent.surface_for(surface_kind, word=focus)
    except Exception:
        surface = None
    if not surface:
        surface = f'I do not understand "{focus}" — what do you mean?'

    # graph record: a clarification (repair) first-pair-part that expects a reply.
    mid = agent.s.add_node("Message", {"from": "agent", "text": surface,
                                       "trouble_source": focus})
    try:
        sa = agent._concept_by_name("clarification")
    except Exception:
        sa = None
    if sa is None:
        sa = agent.s.add_node("Concept", {"name": "clarification"})
    agent.inner.add_edge_unchecked(mid, "has_speech_act", sa)
    agent.inner.add_edge_unchecked(agent.agent, "sent", mid)
    if inbound is not None:
        agent.inner.add_edge_unchecked(mid, "responds_to", inbound)
    try:
        agent.inner.set_attr(mid, "expects_response", True)
    except Exception:
        pass

    return {"asked": True, "reply": surface, "route": "ask_back", "focus": focus,
            "message": mid, "served_by": "host_wiring",
            "note": "a repair first-pair-part (clarification speech act) quoting the "
                    "real trouble source; no content synthesized for the by-position gap"}


# --- WORDPLAY / SATISFIABLE / HONEST-NO-WORLD delivery ------------------------
#
# Mechanical delivery of comprehend_text's new robust-routing dispatches. The
# CONTENT is the faculty's own computation (the morphology-inferred gloss, the
# real held rule, the honest world-limit); this module only reads it back and
# records the graph event. No decision over graph state.

def wordplay_reply(agent, comp, inbound=None) -> dict:
    """Deliver the WORDPLAY reply for a comprehended coinage: the wordplay
    faculty infers a playful reading FROM SHAPE (flagged as inference) and
    composes the reply, register-shaped. Mints a Coinage node (the "engaged it"
    record). The reading is the faculty's; this only reads it back."""
    from domains import wordplay as _wp
    d = comp.dispatch or {}
    analysis = d.get("analysis")
    if not analysis:
        return {"acted": False, "reply": None, "route": "wordplay"}
    try:
        reg = agent.register()
    except Exception:
        reg = "neutral"
    try:
        reply = _wp.compose_reply(agent, analysis, reg)
        gloss = _wp.infer_gloss(analysis)
    except Exception:
        return {"acted": False, "reply": None, "route": "wordplay"}
    node = None
    try:
        node = agent.s.add_node("Coinage", {
            "word": analysis.get("word", ""), "kind": analysis.get("kind", ""),
            "inferred_gloss": gloss, "source": "wordplay"})
        agent.inner.add_edge_unchecked(agent.agent, "engaged", node)
    except Exception:
        node = None
    return {"acted": reply is not None, "reply": reply, "route": "wordplay",
            "coinage": analysis.get("word"), "analysis_kind": analysis.get("kind"),
            "inferred_gloss": gloss, "node": node,
            "served_by": "wordplay_faculty",
            "note": "a shape-inferred playful reading (morphology/sound), flagged as "
                    "inference — not a fabricated dictionary definition"}


def satisfiable_reply(agent, comp, inbound=None) -> dict:
    """Answer an instruction SATISFIABLE from held data. 'rules' -> NAME one held
    RuleSummary (real graph data, via self_model's own describer); 'organisation'
    -> the self_organisation reflective faculty -> produced prose. Never 'understood'."""
    d = comp.dispatch or {}
    target = d.get("target")
    if target == "rules":
        from domains import self_model as _sm
        rs = [n for n in agent.s.nodes("RuleSummary") if agent.inner.has_node(n)]
        if not rs:
            return {"acted": False, "reply": None, "route": "satisfiable"}
        picked = sorted(rs, key=lambda n: (agent.s.node(n)["attrs"].get("name") or ""))[0]
        at = agent.s.node(picked)["attrs"]
        name = at.get("name")
        # `_describe_rule_summary` opens with "my rule 'X' is ..."; lead with
        # "One of them —" so the named rule reads as fluent prose, no stutter.
        reply = "One of them — " + _sm._describe_rule_summary(at)
        goal = _mint_goal(agent, "name_rule", "name", name, inbound=inbound)
        return {"acted": True, "reply": reply, "route": "satisfiable",
                "goal": goal, "goal_kind": "name_rule",
                "rule_name": name, "served_by": "self_model:rules",
                "note": "named a real held RuleSummary from my own self-model"}
    if target == "organisation":
        from domains import reflective_faculty as _rf
        try:
            state = _rf.reflect("self_organisation", None, agent.s)
            reply = agent._surface_self_state(state)
        except Exception:
            reply = None
        goal = _mint_goal(agent, "report_self", "report", "organisation", inbound=inbound)
        return {"acted": reply is not None, "reply": reply, "route": "satisfiable",
                "goal": goal, "goal_kind": "report_self",
                "served_by": "self_model:self_organisation",
                "note": "answered from my self_organisation faculty over real state"}
    return {"acted": False, "reply": None, "route": "satisfiable"}


def honest_no_world_reply(agent, comp, inbound=None) -> dict:
    """A perception request with no world attached -> the HONEST 'no world to
    perceive' reply (never 'understood'). Mints the Goal (the request became a
    goal) and reports the honest action-space limit."""
    d = comp.dispatch or {}
    pred = (d.get("predicate") or "perceive")
    goal = _mint_goal(agent, "instruction", pred, None, inbound=inbound)
    reply = (f"I took on the goal to {pred} what I perceive, "
             "but I have no world attached to perceive right now.")
    return {"acted": True, "reply": reply, "route": "honest_no_world",
            "goal": goal, "goal_kind": "instruction", "served_by": "host_wiring",
            "note": "honest world-limit: a perception request with no scene attached"}


# --- SENSE OF REFERENCE / HUMOUR — the manifold-conditioned + benign-incongruity senses --------
#
# Mechanical delivery of the two SENSE faculties. The CONTENT is the faculty's own computation (the
# manifold-conditioned reference verdict / the benign-incongruity read); this module only reads it
# back, records the graph event, and speaks the composed reply. No decision over graph state.

def reference_reply(agent, comp_or_text, inbound=None) -> dict:
    """Deliver a manifold-conditioned REFERENCE recognition. Decode the turn against the referent
    codebook, CONDITIONED on the tracked interlocutor's manifold (Build-2 snapshot). Fires ONLY when
    a reference is RECOGNIZED as LIVE for this manifold (a niche allusion whose world is live, or a
    graduated concept) — a plain speech pattern returns reply=None so the normal path handles it.
    Own-name recognition (jabberwock -> Carroll) fires regardless of manifold. Returns the reply."""
    from domains import sense_of_reference as _ref
    text = comp_or_text if isinstance(comp_or_text, str) else getattr(comp_or_text, "raw", "")
    try:
        reg = agent.register()
    except Exception:
        reg = "neutral"

    # OWN NAME — the deepest reference: it is named after Carroll.
    own = None
    try:
        own = _ref.recognize_own_name(text)
    except Exception:
        own = None
    if own is not None:
        reply = own["statement"]
        node = None
        try:
            node = agent.s.add_node("ReferenceRecognition",
                                    {"phrase": own["phrase"], "source": own.get("source"),
                                     "reply": reply,
                                     "own_name": True, "source_kind": "own_name"})
            agent.inner.add_edge_unchecked(agent.agent, "recognized", node)
        except Exception:
            node = None
        return {"acted": True, "reply": reply, "route": "reference", "own_name": True,
                "phrase": own["phrase"], "source": own.get("source"), "node": node,
                "served_by": "sense_of_reference:own_name",
                "note": "recognized my own name as an allusion to Carroll (the deepest reference)"}

    interlocutor = agent._interlocutor_snapshot()
    verdict = None
    try:
        verdict = _ref.decode_reference(interlocutor, text)
    except Exception:
        verdict = None
    if not verdict or not verdict.get("recognized"):
        # no reference, or a plain speech pattern for THIS manifold -> let the normal path answer.
        return {"acted": False, "reply": None, "route": "reference",
                "verdict": (verdict or {}).get("liveness")}
    composed = _ref.compose_reference_reply(verdict, reg)
    reply = composed.get("reply")
    if reply is None:
        return {"acted": False, "reply": None, "route": "reference"}
    node = None
    try:
        node = agent.s.add_node("ReferenceRecognition",
                                {"phrase": verdict["phrase"], "source": verdict.get("source"),
                                 "reply": reply,
                                 "liveness": verdict.get("liveness"),
                                 "manifold_type": verdict.get("manifold_type"),
                                 "compelled": False, "source_kind": "reference"})
        agent.inner.add_edge_unchecked(agent.agent, "recognized", node)
    except Exception:
        node = None
    return {"acted": True, "reply": reply, "route": "reference",
            "phrase": verdict["phrase"], "source": verdict.get("source"),
            "liveness": verdict.get("liveness"), "manifold_type": verdict.get("manifold_type"),
            "compelled": composed.get("compelled", False),
            "is_trigger": composed.get("is_trigger", False), "node": node,
            "served_by": "sense_of_reference",
            "note": "reference-liveness decoded against THIS interlocutor's manifold (collapse "
                    "residual); compelled by no phrase — the agent chooses"}


def humour_reply(agent, comp_or_text, inbound=None) -> dict:
    """Deliver a benign-incongruity HUMOUR recognition. Fires ONLY when the turn is recognized as
    humorous (an incongruity that resolves benignly); responds IN KIND (play along / top it), never
    a literal parse. A non-humorous / hostile turn returns reply=None (normal path). Returns reply."""
    from domains import sense_of_humour as _hum
    text = comp_or_text if isinstance(comp_or_text, str) else getattr(comp_or_text, "raw", "")
    try:
        reg = agent.register()
    except Exception:
        reg = "neutral"
    interlocutor = None
    try:
        interlocutor = agent._interlocutor_snapshot()
    except Exception:
        interlocutor = None
    analysis = None
    try:
        analysis = _hum.detect_humour(text, interlocutor)
    except Exception:
        analysis = None
    if not analysis or not analysis.get("humorous"):
        return {"acted": False, "reply": None, "route": "humour"}
    reply = _hum.compose_in_kind(analysis, reg)
    node = None
    try:
        node = agent.s.add_node("HumourRecognition",
                                {"kind": analysis.get("kind"), "benign": True,
                                 "in_kind": True})
        agent.inner.add_edge_unchecked(agent.agent, "recognized", node)
    except Exception:
        node = None
    return {"acted": True, "reply": reply, "route": "humour", "kind": analysis.get("kind"),
            "benign": analysis.get("benign"), "node": node,
            "served_by": "sense_of_humour",
            "note": "recognized a benign incongruity and responded in kind (not literally)"}


__all__ = ["act_on_instruction", "ask_back", "is_ask_back", "attach_scene",
           "wordplay_reply", "satisfiable_reply", "honest_no_world_reply",
           "reference_reply", "humour_reply"]

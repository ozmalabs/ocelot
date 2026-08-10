"""situation_model_to_method — MAP the DEEP reader's situation model onto a
MethodModel, so the agent can source a procedure from DEEP-COMPREHENDING a held
concept's definition (not the shallow procedural_reader's toy grammar).

The deep comprehension reader (comprehension_reader.read_and_comprehend) turns
prose into a SITUATION MODEL: `SmEvent` nodes carrying a lemmatised `verb`, an
`arg1`, and thematic-role edges (`-agent->`, `-theme->`, `-goal->` to `SmEntity`
nodes) plus a temporal index (`idx_time`). This module is a MECHANICAL STRUCTURAL
TRANSLATION from that graph representation to the `method_synthesis` MethodModel
shape (`{name, steps:[{main, trigger}]}`) the existing read->synthesise->validate
->adopt loop already consumes. It makes NO decision over graph state that picks
agent behaviour: it reads the SmEvents already committed by the reader's own
collapse, looks each event VERB's effect KIND up in the HELD procedural-grammar
vocabulary (Concept.proc_effect — the SAME graph data procedural_reader reads,
NOT a Python map), and threads the thematic roles into the MethodModel's
source/target/patient slots. Every meaning was decided upstream by the deep
reader; this only re-expresses it in the synthesiser's vocabulary.

The mapping (STRUCTURAL, over the event's roles — reported honestly where lossy):

  event VERB            -> effect KIND     via held proc_effect vocab
                                           (add/create/insert -> add_edge;
                                            remove/delete/drop -> del_edge;
                                            mark/set -> set_attr;
                                            recompute/refresh -> recompute)
  -agent-> entity       -> the source role (the operation's actor / container)
  -theme-/-goal-> entity-> the patient + target role (the thing acted on)
  a temporal SmEvent    -> a trigger       (best-effort; usually lossy — reported)

For an add_edge / del_edge effect the MethodModel is SELF-CONTAINED (needs no
binding): the source->target anchor relation and the affected edge type are
minted as mechanical name transforms of the comprehended agent/theme nouns (the
exact same category as method_synthesis._titlecase deriving a node TYPE from a
role noun), and an explicit `relation` step binds source<->target so the
synthesiser reads the anchor off the model.

Where the 2-role situation model lacks the structure a synthesiser effect needs
(set_attr wants a STATE complement the SVO event does not carry; recompute wants
an AGGREGATE + dependency the event does not define) this WALLS honestly — the
deep reader gives WHAT the operation does, not the extra role structure those two
effects require. That wall is a finding, not a bug.

ARCHITECTURE (CLAUDE.md): a world-adapter / builder. It reads graph data
(SmEvents + held vocab) and emits graph-shaped MethodModel data. No rule engine,
no agent state, no if/else selecting agent behaviour — the effect KIND is a held-
vocab lookup, the roles are the reader's own edges.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import procedural_reader as pr


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", None)
    return sub, native


def _nid(n) -> int:
    v = getattr(n, "value", None)
    if isinstance(v, int):
        return v
    return int(str(n).lstrip("#"))


def _san(noun: Optional[str]) -> str:
    """Mechanical name transform of a comprehended noun into an edge-safe token
    (lower snake, alnum only) — same category as method_synthesis._titlecase."""
    s = "".join(c if (c.isalnum() or c == "_") else "_" for c in str(noun or "x").lower())
    return "_".join(t for t in s.split("_") if t) or "x"


def _effect_vocab(agent) -> dict:
    """{verb_lemma: effect_kind} read off the HELD procedural grammar (Concept
    nodes carrying proc_role='effect_verb' + proc_effect). Graph data, not a
    Python literal — teaching a synonym is dropping a Concept."""
    pr.ensure_proc_grammar(agent)
    vocab = pr.held_proc_vocab(agent)
    return {w: m.get("proc_effect") for w, m in vocab.items()
            if m.get("proc_role") == "effect_verb" and m.get("proc_effect")}


# --------------------------------------------------------------------------- #
#  parse-correction lexicon — HELD, AGENT-TEACHABLE (the generic fixing ability)
# --------------------------------------------------------------------------- #
# The narrative-tuned deep reader mis-parses terse TECHNICAL prose: it can hand
# an SmEvent a preposition as its verb ("log changes TO data files" -> verb='to'),
# a NOMINALIZED operation as a theme ("LRU eviction" -> theme='eviction'), or a
# non-referential PLACEHOLDER as its agent ("Ratio of bytes written ..." ->
# agent='you') when a clause has no bindable subject. This module cannot re-run
# the reader's parse (comprehension_reader is off-limits / narrative-byte-sacred),
# but it CAN consult a held, agent-taught PARSE-CORRECTION LEXICON when it maps
# SmEvents -> a MethodModel. Three Concept classes, all graph data the agent MINTS
# via teach() (never a Python literal word-list):
#
#   proc_role='preposition'  (function word) -> NOT an operation; never a verb.
#   proc_role='nominal_of' + base=<verb>     -> a nominalized surface (eviction)
#                                               maps to its base effect verb (evict).
#   proc_role='placeholder'  (you/it/they/one)-> a dummy subject the reader inserts
#                                               when it found no real agent; an event
#                                               with a placeholder agent is REJECTED
#                                               (the concept is NOT the verb's actor).
#
# The consultation is a MECHANICAL FILTER/lookup over that held data (no decision
# hardcoded here): teaching a Concept extends the correction; this only reads it.
_PREP_ROLES = frozenset({"preposition", "function_word", "role_prep"})
_PLACEHOLDER_ROLES = frozenset({"placeholder", "pronoun", "dummy_subject"})


def _parse_correction_lexicon(agent):
    """Read the HELD parse-correction Concepts off the graph:
      prepositions  -> set of function-word surfaces (skip as a verb candidate)
      placeholders  -> set of dummy-subject surfaces (reject as an agent)
      nominals      -> {nominalized_surface: base_effect_verb}
    Graph-resident, agent-taught. ensure_proc_grammar loads the taught seed
    on-demand (the same non-resident companion the effect-verb vocab uses), so a
    fresh boot holds whatever the agent has minted."""
    pr.ensure_proc_grammar(agent)
    sub, _ = _resolve(agent)
    preps, placeholders, nominals = set(), set(), {}
    for n in sub.nodes("Concept"):
        at = sub.node(n)["attrs"]
        role = at.get("proc_role")
        if not role:
            continue
        nm = str(at.get("name", "")).lower()
        if not nm:
            continue
        if role in _PREP_ROLES:
            preps.add(nm)
        if role in _PLACEHOLDER_ROLES:
            placeholders.add(nm)
        if role == "nominal_of" and at.get("base"):
            nominals[nm] = str(at.get("base")).lower()
    return preps, placeholders, nominals


def read_situation_events(agent, *, unit: Optional[int] = None) -> list:
    """Read the SmEvents the deep reader minted, in temporal order, each as
    {verb, agent, theme, arg1, idx_time, active, unit}. Pure graph read of the
    situation model — the reader already decided every field."""
    sub, native = _resolve(agent)
    gd = sub.graph_to_dict()
    ntype = {n["id"]: n for n in gd["nodes"]}
    events = []
    for n in sub.nodes("SmEvent"):
        a = sub.node(n)["attrs"]
        if unit is not None and a.get("unit") != unit:
            continue
        nid = _nid(n)
        roles = {}
        for e in gd["edges"]:
            if e.get("src") == nid and e.get("type") in ("agent", "theme", "goal", "source"):
                tgt = ntype.get(e.get("tgt"))
                if tgt is not None:
                    roles[e["type"]] = tgt.get("attrs", {}).get("name")
        events.append({
            "verb": a.get("verb"),
            "agent": roles.get("agent"),
            "theme": roles.get("theme") or roles.get("goal"),
            "arg1": a.get("arg1"),
            "idx_time": a.get("idx_time", a.get("t")),
            "active": a.get("active"),
        })
    events.sort(key=lambda ev: (ev["idx_time"] is None, ev["idx_time"]))
    return events


def situation_model_to_method(agent, *, name: str = "method",
                              unit: Optional[int] = None) -> dict:
    """Translate the deep reader's situation model (already on the graph) into a
    MethodModel for method_synthesis. Returns {name, steps, main_event, effect,
    events} or {wall, reason, events}.

    The FIRST SmEvent that resolves to an action (through the held parse-correction
    lexicon — see `_parse_correction_lexicon`) is the action; its agent/theme fill
    source/target/patient. add_edge/del_edge emit a self-contained relation step
    (zero binding). set_attr / recompute WALL honestly — the SVO situation model
    does not carry the state / aggregate role they need.

    Parse-correction consultation (GAP A + GAP B, all held graph data):
      · an event whose VERB is a held preposition is skipped (not an operation);
      · an event whose AGENT is a held placeholder (the reader's dummy subject) is
        rejected — the effect verb has no genuine actor, so the concept is NOT it
        (this drops the "bytes written" / write_amplification family of FPs);
      · an event whose VERB is a held effect verb IS the action; else an event
        whose THEME/arg1 is a held nominalization maps to that nominalization's
        base effect verb (eviction -> evict), recovering an operation the
        narrative reader buried as a noun.
    """
    eff_vocab = _effect_vocab(agent)
    preps, placeholders, nominals = _parse_correction_lexicon(agent)
    events = read_situation_events(agent, unit=unit)

    def _agent_ok(ev) -> bool:
        # GAP A — the concept must be the actor: reject the reader's non-referential
        # dummy-subject placeholder (you/it/they/one). A real content-noun agent
        # (block, cache, compaction, queue) passes.
        ag = (ev.get("agent") or "").lower()
        return bool(ag) and ag not in placeholders

    main_ev = None
    verb = None
    effect = None
    source_note = ""
    for ev in events:
        v = (ev.get("verb") or "").lower()
        if v in preps:                      # GAP B — a preposition is not a verb
            continue
        if not _agent_ok(ev):               # GAP A — dummy subject, not the concept
            continue
        if not ev.get("theme") or not ev.get("agent"):
            continue
        if v in eff_vocab:                  # direct held effect verb
            main_ev, verb, effect = ev, ev["verb"], eff_vocab[v]
            break
        # GAP B — a nominalized operation the reader parked in the theme/arg1
        # ("LRU eviction" -> theme 'eviction'): map the surface to its base
        # effect verb, only when that base is itself a held effect verb.
        hit = None
        for slot in ("theme", "arg1"):
            surf = (ev.get(slot) or "").lower()
            if surf in nominals and nominals[surf] in eff_vocab:
                hit = (surf, nominals[surf])
                break
        if hit is not None:
            surf, base = hit
            main_ev, verb, effect = ev, base, eff_vocab[base]
            source_note = ("nominalization %r -> base effect verb %r (held "
                           "nominal_of vocab)" % (surf, base))
            break
    if main_ev is None:
        return {"wall": "no actionable event in the situation model",
                "reason": ("the deep read yielded no SmEvent that resolves to an "
                           "operation under the held parse-correction lexicon — a "
                           "declarative concept (knows-WHAT, not knows-HOW), an "
                           "agentless clause the reader parked on a placeholder "
                           "subject, or prose too telegraphic / mis-parsed for the "
                           "narrative-tuned reader (a buried verb / noun-list the "
                           "adapter cannot reach)"),
                "events": events}

    agent_noun = main_ev["agent"]
    theme_noun = main_ev["theme"]

    # add_edge / del_edge — SELF-CONTAINED: agent->source, theme->target, a minted
    # anchor relation + affected edge type (mechanical name transforms of the
    # comprehended nouns), plus a relation step so the synthesiser reads the anchor.
    if effect in ("add_edge", "del_edge"):
        etype = "has_" + _san(theme_noun)
        anchor = "assoc_" + _san(agent_noun) + "_" + _san(theme_noun)
        main = {"kind": "action", "effect": effect, "verb": verb,
                "patient": theme_noun, "node_type": None, "edge_type": etype,
                "object_kind": "edge",
                "roles": {"source": agent_noun, "target": theme_noun},
                "condition": None}
        rel_step = {"sentence": "%s %s %s" % (agent_noun, verb, theme_noun),
                    "step_index": 0,
                    "trigger": None,
                    "main": {"kind": "relation", "subject": agent_noun,
                             "object": theme_noun, "relation": anchor}}
        act_step = {"sentence": "%s %s %s" % (agent_noun, verb, theme_noun),
                    "step_index": 1, "trigger": None, "main": main}
        return {"name": name, "steps": [rel_step, act_step],
                "main_event": main_ev, "effect": effect, "events": events,
                "how": ("verb %r -> effect %s (held proc_effect vocab); agent %r -> "
                        "source, theme %r -> target+patient; anchor rel %r + edge "
                        "%r minted from the comprehended nouns%s"
                        % (verb, effect, agent_noun, theme_noun, anchor, etype,
                           ("; " + source_note) if source_note else ""))}

    # set_attr — needs a STATE complement the SVO event does not carry.
    if effect == "set_attr":
        return {"wall": "set_attr needs a state complement the situation model "
                        "does not carry", "reason": ("the deep read gives verb %r + "
                        "patient %r but no STATE word (the SVO event has agent+theme, "
                        "not patient+state) — set/mark WALLS: WHAT is set, not to WHAT"
                        % (verb, theme_noun)), "effect": effect, "events": events}

    # recompute — needs an aggregate + dependency the event does not define.
    if effect == "recompute":
        return {"wall": "recompute needs an aggregate + dependency relation the "
                        "situation model does not define",
                "reason": ("the deep read gives verb %r + patient %r but no "
                           "AGGREGATE (count/sum) nor a 'view depends on source' "
                           "relation — recompute WALLS on the missing structure"
                           % (verb, theme_noun)),
                "effect": effect, "events": events}

    return {"wall": "unmapped effect kind %r" % effect, "effect": effect,
            "events": events}


__all__ = ["read_situation_events", "situation_model_to_method"]

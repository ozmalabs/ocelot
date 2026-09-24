"""comprehend_text — the GENERAL comprehension FRONT END: arbitrary text -> a
structured Comprehension{kind, focus, intent, dispatch, gaps} the world adapter
(or the follow-on conversation-action machinery) acts on.

THE PROBLEM this replaces: `domains/comprehend_question.py`'s `comprehend()` is
a table of 7-ish whole-sentence CONSTRUCTIONS (`comprehend_meta` / `comprehend_
know` / `comprehend_compound` / `comprehend_compare`) matched against a FIXED
surface-fragment lexicon (`seeds/question_targets.json`). Input that matches no
canned shape returns `grounded=False` -> the chat falls back to "acknowledgment"
even though the agent ALREADY HAS a general language faculty: POS-typing (the
Wiktionary + function-word reference), the gap-as-part-of-speech parser
(`construction_grammar.parse_with_gaps`), and a relation composer
(`compose_relation` / `render_relation` / `resolve_focus`). This module is
WIRING, not new NLU — it routes arbitrary text through that existing machinery
and REASONS over the resulting frame to derive an intent, instead of matching
canned constructions.

THE CONTRACT

    comprehend_text(agent, text) -> Comprehension

`agent` is a WorldAdapter (or any object with a `.s` substrate attribute, or a
bare substrate — `getattr(agent, "s", agent)` resolves it). Steps:

  1. FAST PATH — try the held construction TABLE first
     (`comprehend_question.comprehend`). When it GROUNDS, that shape is already
     correctly handled; wrap it (`Comprehension.fastpath=True`,
     `dispatch={"path": "table", "spec": <TargetSpec>}`) and stop. This is the
     regression-safety net: every phrasing the table already understands keeps
     its EXACT existing behaviour (the caller still drives the SAME reflect() /
     answer_about() backend off the SAME TargetSpec).

  2. GENERAL PATH — when the table does NOT ground the text, POS-type every
     token via the agent's OWN faculty and parse it into a typed-gap FRAME
     (`construction_grammar.parse_with_gaps`): a wh-FOCUS (if any) + a
     function-word skeleton + the content/unknown spans as TYPED GAPS. Compose
     the frame into a {predicate, subject, object, oblique} RELATION
     (`compose_relation`) when useful.

  3. REASON over the frame to derive KIND + DISPATCH — never a canned match:

     - INTERROGATIVE: the text ends with `?`, OR the FIRST element is a
       copula/auxiliary (subject-aux inversion — "Can you ...?", "Is that
       ...?"), OR a wh-FOCUS leads the clause (no verb precedes it). ->
       `kind="question"`.
         * REFLEXIVE (the question is ABOUT THE AGENT): a self-reference cue
           ("you"/"your"/"yourself"/"yours"/"me" — the SAME cue set
           `comprehend_question` gates its meta table on) is present, OR a
           gap token names a RuleSummary actually HELD in the graph (a
           DISCOVERED fact, not a guess — `self_model._find_rule_summaries`).
           A held rule name is the strongest signal and wins outright. Then:
             (a) rule name grounded -> `self_model_rule` (self_model faculty),
                 `meta_arg` = the rule name;
             (b) else score every entry in the SAME held meta lexicon
                 (`comprehend_question.load_meta_lexicon`) by how many of its
                 match/any fragments appear ANYWHERE in the frame's tokens
                 (an OVERLAP score, not the table's all-fragments-in-order
                 requirement) and take the best-scoring entry — this is what
                 lets a paraphrase ("what's your shape") or an insertion
                 ("what kind of shape do you have") reach the SAME meta_target
                 the table's exact fragment would;
             (c) else (reflexive, interrogative, but no keyword scores) fall
                 back to a DEFAULT meta_target keyed on the wh-role
                 (`_WH_DEFAULT_META` — "how" -> self_organisation, "what" ->
                 self_identity, "which" -> self_shape, "why" -> frontier).
                 This is a choice of WHICH held, read-only faculty to consult
                 (always a real graph query, honestly reported), never a
                 fabricated answer.
           `dispatch = {"path": "meta", "meta_target": ..., "meta_arg": ...,
           "strategy": "rule_name_grounded" | "keyword_overlap" |
           "wh_default"}`.
         * Otherwise (a WORLD question): the composed relation's subject/
           object/oblique nominal is the TOPIC; `resolve_focus` is tried over
           it (a learned answer or a held edge — no subgoals available at this
           synchronous layer, so its bare-definitional branch will not fire
           here); `dispatch = {"path": "know", "concept": topic, "pre_resolved":
           ...}`.
         * If neither a reflexive dispatch nor a topic nominal can be derived,
           `dispatch = {"path": "frontier", "reason": ...}` — an honest,
           well-posed comprehension gap, never a faked target.

     - IMPERATIVE: the FIRST element is a bare content VERB (no subject/aux
       precedes it) and the text is not already classified a question above.
       -> `kind="instruction"`, `dispatch={"path": "instruction", "relation":
       compose_relation(frame), "predicate": ..., "object": ...}` — the intent
       the follow-on conversation-action task turns into a goal/action.
       EXCEPTION: if a gap token names a HELD rule (the same discovery as
       2a above), the imperative is actually an indirect information request
       ("Tell me about the rule X") -> promoted to `kind="question"` with the
       same `self_model_rule` dispatch as the reflexive case. This mirrors an
       existing project precedent (`world_adapter._QUESTION_LEADS` already
       treats a bare "tell"-led line as a question, not a command).

     - DECLARATIVE (anything else): `kind="statement"`,
       `dispatch={"path": "statement", "relation": compose_relation(frame)}`.

  4. TYPED GAPS are ALWAYS carried on the return (`Comprehension.gaps`, the
     SAME `parse_with_gaps` gap list: `{"surface", "pos"}` per content/unknown
     span) — the first-class, honest "what I don't yet know how to ground"
     record. Nothing here fabricates an answer FROM a gap; a gap the dispatch
     step could not resolve into a topic/meta_target stays `path="frontier"`.

WHAT THIS MODULE DOES NOT DO (CLAUDE.md world-adapter discipline): it does not
call `reflective_faculty.reflect`, does not render a reply, does not touch
graph state, and holds no state of its own — it is a pure function of
(substrate-read-only, text) -> Comprehension. The caller (`WorldAdapter.
answer_question`) SEQUENCES the dispatch (calls `reflect()` / `answer_about()`
off the derived meta_target/concept) exactly as it already did for the table
path; this module only decides WHICH held faculty and WHAT argument, by
reasoning over the parse, not by matching a fixed sentence shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from domains import construction_grammar as _cg
from domains import comprehend_question as _cq
from domains import instruction_reading as _ir
from domains import self_model as _self_model
from domains import wordplay as _wp
from domains import preposition_roles as _prep_roles

# Leading DISCOURSE / POLITENESS markers — closed-class reference fact (the same
# shape as function_word_reference's closed copula/aux table). Sentence-initial
# "Pray,"/"kindly"/"prithee"/"please" are politeness markers, NOT content verbs;
# the parser would otherwise read "Pray" as an imperative verb and build a bogus
# instruction ("Pray the nature"). They are stripped before parsing so the
# ornate question/instruction underneath reaches its real intent.
_POLITENESS_MARKERS = frozenset({"pray", "kindly", "prithee", "please"})

# Leading imperative verbs that ENUMERATE / REPORT HELD DATA (name/list one of X)
# — a satisfiable instruction the agent answers from its own graph, not an act.
_ENUMERATE_VERBS = frozenset({"name", "list", "enumerate"})

# Held-data nouns an enumerate-instruction can target -> the held faculty that
# answers it (a real, read-only graph query; never fabricated).
_SATISFIABLE_TARGET = {
    "rule": "rules", "rules": "rules",
    "domain": "organisation", "domains": "organisation",
    "faculty": "organisation", "faculties": "organisation",
    "organisation": "organisation", "organization": "organisation",
    "capability": "organisation", "capabilities": "organisation",
}

_MODAL_REQUEST_PREFIXES = frozenset({"can", "could", "would", "will"})

# Leading verbs that request an ACCOUNT (describe/report ...) — paired with a
# PERCEPTION cue and NO attached scene, this is the honest "no world to perceive"
# case, not a self-report and not an "understood" ack.
_ACCOUNT_VERBS = frozenset({"describe", "tell", "report", "explain", "say",
                            "show", "state", "account"})
_PERCEPTION_CUES = frozenset({"perceive", "see", "seeing", "look", "looking",
                              "around", "there", "scene", "observe", "view",
                              "front", "behind", "watch", "sense"})

# The SAME self-reference cue set comprehend_question gates its meta table on
# (data, not table logic) — a question carrying one of these is ABOUT the agent.
_SELF_CUES = _cq._SELF_CUES

# A reflexive interrogative with NO keyword-overlap hit still needs a faculty
# to consult; default it off the wh-ROLE (not the surface word) so a paraphrase
# lands on a sensible held faculty instead of a wall. Every value here is a
# key already present in `reflective_faculty._DISPATCH`.
_WH_DEFAULT_META = {
    "reason": "frontier",
    "manner": "self_organisation",
    "thing": "self_identity",
    "agent": "self_identity",
    "selection": "self_shape",
}

# Verbs of TELLING whose imperative use is pragmatically an information
# request ("Tell me about X") — kept only as documentation of the intuition;
# the actual promotion below fires on a GROUNDED rule name, not this list, so
# it never guesses.


@dataclass
class Comprehension:
    raw: str
    kind: str = "statement"                 # "question" | "instruction" | "statement"
    focus: Optional[str] = None             # wh-role (reason/thing/manner/time/place/selection/agent) or None
    reflexive: bool = False                 # is this ABOUT the agent itself?
    intent: str = ""                        # short human-readable intent label
    dispatch: dict[str, Any] = field(default_factory=dict)
    gaps: list[dict] = field(default_factory=list)
    frame: Optional[dict] = None            # the raw parse_with_gaps frame (general path only)
    relation: Optional[dict] = None         # compose_relation(frame), when computed
    fastpath: bool = False                  # did the OLD comprehend_question table already ground this?
    table_spec: Any = None                  # the TargetSpec, when fastpath
    note: str = ""

    def line(self) -> str:
        if self.fastpath:
            return f"{self.raw[:60]!r} -> [TABLE FAST-PATH] {self.table_spec.line()}"
        d = self.dispatch
        return (f"{self.raw[:60]!r} -> [{self.kind.upper()}] focus={self.focus} "
                f"reflexive={self.reflexive} dispatch={d.get('path')} "
                f"gaps={[g['surface'] for g in self.gaps]}")


def _all_words(frame: dict) -> set[str]:
    return {e["surface"].lower().strip(",.;:?!") for e in frame.get("elements", [])}


def _has_self_cue(frame: dict) -> bool:
    return any(w in _SELF_CUES for w in _all_words(frame))


def _detect_reflexive_rule(substrate: Any, gaps: list[dict]) -> Optional[str]:
    """A gap token that names a RuleSummary ACTUALLY HELD in the graph — a
    discovered fact (not a guess): `self_model._find_rule_summaries` is the
    SAME exact-match lookup `self_model_rule` answers from. Returns the
    surface that hit, or None."""
    if substrate is None:
        return None
    for g in gaps:
        surf = (g.get("surface") or "").strip(",.;:?!")
        if len(surf) < 3:
            continue
        try:
            hits = _self_model._find_rule_summaries(substrate, surf)
        except Exception:
            hits = []
        if hits:
            return surf
    return None


# MOVED to domains/comprehend_question.py (2026-08-14, SHAPE_AUDIT.md §7
# finding #10 / instance 3: this was a byte-for-byte duplicate of lexicon-
# matching logic that belongs with the lexicon it scores). Thin re-exports so
# this module's one call site (below) and any external caller by this name
# keep working unchanged.
_score_meta_entry = _cq._score_meta_entry
_best_meta_entry = _cq._best_meta_entry


def _capture_meta_arg(entry: dict, text: str) -> Optional[str]:
    toks = _cq._tokens(text)
    anchor = entry.get("arg_after")
    if anchor:
        return _cq._arg_after(toks, anchor)
    between = entry.get("arg_between")
    if between:
        return _cq._arg_between(toks, between.get("start") or [], between.get("end") or [])
    if entry.get("goal_from_question"):
        return text
    return None


def _first_element(frame: dict) -> Optional[dict]:
    els = frame.get("elements") or []
    return els[0] if els else None


def _classify_kind(text: str, frame: dict) -> str:
    """INTERROGATIVE / IMPERATIVE / DECLARATIVE — from the parsed frame's
    shape, not a sentence-shape table. Ends-with-'?' is the strongest signal
    (mirrors the project's existing I/O-boundary speech-act cue,
    `WorldAdapter.classify_speech_act`); subject-aux inversion and a
    clause-leading wh-focus are the other two GRAMMATICAL interrogative
    signals. A leading bare content verb (no subject/aux before it) is an
    imperative UNLESS one of the interrogative signals already fired (so an
    embedded wh-complement, "describe WHAT you see", stays an instruction —
    the matrix verb "describe" is what governs the sentence's mood).

    MIGRATED (Wave 4): this Python ladder NO LONGER DECIDES on the live path.
    The decision is the seeds/speech_act_classify.json rules (sak_kind_*),
    run by the Rust rule engine — over the LIVE inbound Message in converse()
    (WorldAdapter._graph_kind_for) or over a scratch Message here
    (_classify_kind_rules) for direct callers. This body is retained ONLY as
    (a) the fixture-capture oracle (tests/fixtures/speech_act_parity/capture.py)
    and (b) the no-native-substrate fallback, per the module's established
    `_holds` fallback discipline. The parity gate
    (tests/test_speech_act_parity_migrated.py) pins rules ≡ this ladder;
    the audit gate (tests/test_comprehension_decision_audit_migrated.py)
    pins that this body does not execute when the engine is available."""
    ends_q = text.strip().endswith("?")
    first = _first_element(frame)
    first_is_verb = bool(first) and first["role"] == "content" and first["pos"] == "verb"
    first_is_aux = bool(first) and first["role"] == "function" and \
        first["pos"] in ("copula", "auxiliary", "aux")
    leading_wh = bool(first) and first["role"] == "focus"
    if ends_q or first_is_aux or leading_wh:
        return "question"
    if first_is_verb:
        return "instruction"
    return "statement"


# ---------------------------------------------------------------------------
# KIND CLASSIFICATION IS THE GRAPH'S DECISION (Wave 4 migration). The adapter
# (or this module, for direct callers) computes only the SIGNALS — parse data
# the POS layer already derived, no decision — and the seeded
# speech_act_classify rules mint the kind. Two consumption paths:
#   * LIVE (converse): WorldAdapter._graph_kind_for writes the signals onto the
#     live inbound Message, runs a rule pass, and reads sak_kind back — the
#     rules are the agent's OWN held copies (reconciled / refreshable /
#     experimentable), so the kind decision is self-repairable.
#   * DIRECT (comprehend_text called without a live Message, agent may be
#     None): _classify_kind_rules runs the SAME seed rules over a scratch
#     Message via the Rust engine (the _scratch_words/_holds discipline).
# ---------------------------------------------------------------------------

def _signals_of(text: str, frame: dict) -> dict:
    """The three classification signals `_classify_kind` reads, as plain data:
    ends-with-'?' on the (already politeness-stripped) text, and the first
    parsed element's role/pos. Mechanical read of the parse — no decision."""
    first = _first_element(frame or {})
    return {
        "ends_q": bool((text or "").strip().endswith("?")),
        "first_role": first.get("role") if first else None,
        "first_pos": first.get("pos") if first else None,
    }


def kind_signals(agent, text: str) -> dict:
    """Politeness-strip + parse `text` and return the classification signals —
    the adapter-side helper for writing them onto a live inbound Message.
    Mechanical: the strip and the parse are the SAME calls comprehend_text
    makes; nothing here decides the kind."""
    stripped = _strip_politeness(agent, text or "")
    try:
        frame = _cg.parse_with_gaps(stripped, getattr(agent, "s", agent))
    except Exception:  # noqa: BLE001 — unparseable input still classifies (ends-? only)
        frame = {}
    return _signals_of(stripped, frame)


def first_imperative_evidence(agent: Any, text: str, *, first_role: str | None = None,
                              first_pos: str | None = None) -> bool:
    """Read the held verb-head faculty for a politeness-stripped clause.

    This is additional grammatical evidence, not a new lexical command list:
    the first recognized element must be content, and the existing native
    verb-head measure must accept its surface. It covers words whose primary
    POS is adjective/noun but which the language faculty still measures as
    verb-headed (for example ``open``).
    """
    stripped = _strip_politeness(agent, text or "")
    try:
        # This evidence is specifically for a recognized politeness-prefixed
        # imperative whose first content word has a misleading primary POS.
        # Do not broaden the established bare-clause speech-act parity path:
        # words such as ``focus`` and ``rain`` have verb senses but are not
        # thereby directives in an unmarked declarative.
        if stripped == (text or ""):
            return False
        if first_role is None or first_pos is None:
            frame = _cg.parse_with_gaps(stripped, getattr(agent, "s", agent))
            first = _first_element(frame)
            first_role = first.get("role") if first else None
            first_pos = first.get("pos") if first else None
        if first_role != "content":
            return False
        if first_pos == "verb":
            return False
        # The politeness reader has already recognized and removed the leading
        # marker. Read the first remaining surface token mechanically here;
        # avoid a second substrate-backed parse that could perturb the live
        # POS evidence used by the parity path.
        words = _ws_tokens(stripped)
        surface = str(words[0] if words else "").strip(" ,.;:?!")
        if not surface:
            return False
        # Reporting/enumeration imperatives already have dedicated indirect
        # information routes; this evidence is for action-like politeness,
        # not for reclassifying "kindly list ..." as a bare action command.
        if surface.lower() in _ACCOUNT_VERBS | _ENUMERATE_VERBS:
            return False
        return bool(_ir.is_verb_headed(surface))
    except Exception:
        return False


_SAK_RULES_CACHE: Optional[list] = None


def _sak_rules() -> list:
    """The speech_act_classify seed's rules (module-cached; the seed file is
    the canonical source the daemon's reconciliation also reads)."""
    global _SAK_RULES_CACHE
    if _SAK_RULES_CACHE is None:
        from substrate.seed_loader import manifest_for
        _SAK_RULES_CACHE = list(manifest_for("speech_act_classify").get("rules") or [])
    return _SAK_RULES_CACHE


def _classify_kind_rules(signals: dict, rules: Optional[list] = None,
                         *, receipt_sink: Any = None) -> Optional[str]:
    """The KIND decision made by the sak_kind_* rules, run by the Rust rule
    engine over a scratch Message carrying exactly the signal attrs the
    adapter writes on a live turn. `rules` (when given) are the AGENT'S OWN
    HELD rule bodies (exported from its live engine — the self-repairable
    copies); default is the seed file. The pass is ISOLATED on purpose: only
    the kind rules run, so no unrelated rule can fire on a half-ingested turn
    (running the FULL live fixpoint here measurably flipped a downstream rule
    race — the elaboration serve/anaphor tie — which this wave's no-behavior-
    change bar forbids). Returns the minted kind, or None when no native
    substrate is available (the caller then uses the documented
    `_classify_kind` fallback, per the module's `_holds` discipline)."""
    try:
        from substrate_rs import _native
        s = _native.Substrate()
    except Exception:  # noqa: BLE001 — no engine -> caller falls back
        return None
    try:
        ag = s.add_node("Agent", {})
        attrs = {"sak_pending": 1.0,
                 "sak_ends_q": 1.0 if signals.get("ends_q") else 0.0}
        if signals.get("first_role") is not None:
            attrs["sak_first_role"] = str(signals["first_role"])
        if signals.get("first_pos") is not None:
            attrs["sak_first_pos"] = str(signals["first_pos"])
        if signals.get("input_kind") is not None:
            attrs["sak_input_kind"] = str(signals["input_kind"])
        m = s.add_node("Message", attrs)
        s.add_edge_unchecked(ag, "received", m)
        body = rules if rules else _sak_rules()
        s.import_rules([dict(r, active=True) for r in body])
        s.run_rules(100)
        kind = s.node(m)["attrs"].get("sak_kind")
        if kind is None:
            return None
        kind = str(kind)
        # The native scratch substrate is authoritative for this classification:
        # the returned value is read from the rule-written ``sak_kind`` attr,
        # never computed by the adapter.  When this direct-caller path has a
        # live WorldAdapter, preserve that provenance as graph data.  Bare
        # scratch callers intentionally have no sink and therefore produce no
        # fabricated receipt.
        if (receipt_sink is not None and hasattr(receipt_sink, "s")
                and hasattr(receipt_sink, "agent")):
            receipt = receipt_sink.s.add_node("NativeSpeechActReceipt", {
                "schema": "native_speech_act_receipt.v1",
                "cluster": "comprehend_text.speech_act_classification",
                "provenance": "native_rule_readback:speech_act_classification",
                "native_rule": f"sak_kind_{kind}",
                "kind": kind,
                "outcome_source": "native_rule_readback",
                "python_outcome_selection": False,
            })
            try:
                receipt_sink.inner.add_edge_unchecked(
                    receipt_sink.agent, "has_native_speech_act_receipt", receipt)
            except TypeError:
                receipt_sink.inner.add_edge_unchecked(
                    receipt_sink.agent, "has_native_speech_act_receipt", receipt, {})
        return kind
    except Exception:  # noqa: BLE001 — engine hiccup -> caller falls back
        return None


# A closed cue set for a self-STRUCTURE / COMPOSITION question — the thing the
# self_organisation faculty actually answers ("how are you put together / organised
# / composed / made up?"). A manner ("how") question carrying one of these is a
# legitimate structure query and keeps its self_organisation routing; a manner
# question WITHOUT any of these ("how do you learn?", "how does X come about?") is a
# process the agent has no held self-account for -> the honest floor.
_STRUCTURE_CUES = frozenset({
    "organised", "organized", "organise", "organize", "organisation", "organization",
    "structured", "structure", "composed", "compose", "composition", "made", "make",
    "built", "build", "constructed", "construct", "assembled", "assemble", "arranged",
    "arrange", "constituted", "comprised", "comprise", "put", "together",
})


def _asks_self_structure(frame: dict) -> bool:
    """True iff a reflexive 'how' frame is about the agent's STRUCTURE / composition
    ('how are you put together / organised / composed?') — a real self_organisation
    question — rather than a process the agent holds no self-account for."""
    return bool(_all_words(frame) & _STRUCTURE_CUES)


def _is_polar_capability_question(rel: dict) -> bool:
    """True iff a yes/no question asks whether the AGENT can DO something with no
    external object topic ('can you dance?' yes; 'can you play chess?' no — chess
    is the topic and the topic-route handles it). Mechanical relation read only."""
    subj = (rel.get("subject") or {}).get("surface", "").lower().strip(",.;:?!")
    pred = rel.get("predicate")
    if subj not in _SELF_CUES or not pred:
        return False
    if pred.get("role") != "content" or pred.get("pos") != "verb":
        return False
    obj = rel.get("object")
    if obj is None:
        return True
    obj_surf = (obj.get("surface") or "").lower().strip(",.;:?!")
    return obj_surf in _SELF_CUES


def _hypothetical_assumption(frame: dict, raw: str = "") -> str | None:
    """Mechanical read of a counterfactual clause ('if you had a body') on a polar
    capability question. Returns the assumed affordance phrase, or None."""
    import re
    text = raw or " ".join((e.get("surface") or "") for e in (frame.get("elements") or []))
    m = re.search(
        r"\bif\s+(?:you|i)\s+had\s+(?:a |an |the )?(.+?)(?:\?|$|,|\s+would|\s+could|\s+can)",
        text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip("?.,;")
    return None


def _self_process_verb(frame: dict):
    """From a reflexive 'how' frame with no held answer, the process VERB and whether
    its subject is the AGENT (a 'you <content-verb>' adjacency). Used only to PHRASE the
    honest self-process floor ("I can't say precisely how I <verb>" vs the subject-less
    "... how that comes about") — never to fabricate an answer."""
    els = frame.get("elements") or []
    for i in range(len(els) - 1):
        surf = (els[i].get("surface") or "").lower().strip(",.;:?!")
        nxt = els[i + 1]
        if surf in _SELF_CUES and nxt.get("role") == "content" and nxt.get("pos") == "verb":
            return nxt["surface"].strip(",.;:?!"), True
    for e in els:
        if e.get("role") == "content" and e.get("pos") == "verb":
            return e["surface"].strip(",.;:?!"), False
    return None, False


def _topic_nominal(rel: dict) -> Optional[dict]:
    return rel.get("subject") or rel.get("object") or rel.get("oblique")


# These are adapter-side semantic readings, not ontology labels.  The graph
# receives only the language-neutral result (world dependency / deictic
# reference / unresolved selection); another language adapter can emit the
# same fields from its own function-word and construction evidence.
_DEICTIC_DETERMINERS = frozenset({"this", "that", "these", "those"})


def _graph_referent_available(agent: Any, target: str) -> bool:
    """Read whether discourse state already binds a deictic target.

    A lexical Concept is not enough: a deictic expression needs a graph
    relation to the current discourse/world state.  This is deliberately a
    structural read, not a reply or noun-list shortcut.
    """
    substrate = getattr(agent, "s", agent)
    target = str(target or "").strip(".,;:?!").lower()
    if substrate is None or not target:
        return False
    try:
        for node in substrate.nodes("CurrentTopic"):
            if str(substrate.node(node)["attrs"].get("name") or "").lower() == target:
                return True
        for node in substrate.nodes("ReferenceResolutionEvidence"):
            attrs = substrate.node(node)["attrs"]
            if (str(attrs.get("epistemic_status") or "") == "supported"
                    and str(attrs.get("referent") or attrs.get("target") or "").lower()
                    == target):
                return True
    except Exception:
        return False
    return False


def _graph_discourse_binding_available(agent: Any) -> bool:
    """Return whether the graph binds the current discourse topic.

    This is deliberately stronger than seeing a pronoun or a lexical
    ``Concept``.  A current topic must also have an in-focus
    ``DiscourseReferent`` (or a supported reference-resolution evidence
    record).  The result is a language-neutral binding fact for the cognition
    layer; it is not an answer or a surface-text heuristic.
    """
    substrate = getattr(agent, "s", agent)
    if substrate is None:
        return False
    try:
        topics = {
            str(substrate.node(node)["attrs"].get("name") or "").strip().lower()
            for node in substrate.nodes("CurrentTopic")
        }
        topics.discard("")
        if not topics:
            return False
        for node in substrate.nodes("DiscourseReferent"):
            attrs = substrate.node(node)["attrs"]
            concept = str(attrs.get("concept") or "").strip().lower()
            if concept in topics and attrs.get("cognitive_status") == "in_focus":
                return True
        for node in substrate.nodes("ReferenceResolutionEvidence"):
            attrs = substrate.node(node)["attrs"]
            if (attrs.get("epistemic_status") == "supported"
                    and str(attrs.get("concept") or "").strip().lower() in topics):
                return True
    except Exception:
        return False
    return False


def _language_adapter_evidence(agent: Any, frame: Optional[dict], rel: Optional[dict],
                               *, kind: str) -> dict[str, Any]:
    """Emit semantic evidence consumed by graph grounding/arbitration.

    This intentionally does not name English concepts or inspect reply text.
    It reads the adapter's typed frame plus graph-resident discourse support.
    """
    evidence: dict[str, Any] = {}
    frame = frame or {}
    rel = rel or {}
    elements = frame.get("elements") or []

    # A locative/thematic PP is a world-state dependency.  The preposition
    # role comes from the language adapter's held role faculty; the cognition
    # layer sees only `world_dependency=spatial_relation`.
    # An oblique PP is not automatically a world-location dependency.  The
    # same typed relation covers abstract predication ("a gap in your
    # reasoning") and locative questions ("what is beyond the wall?").  Only
    # an interrogative seeking the thing located relative to the oblique can
    # require an attached scene; otherwise the PP is semantic content for the
    # assertion/meta faculty.  This keeps the cognition boundary language
    # neutral: it relies on the adapter's typed focus, not an English phrase
    # or a surface word list.
    if (kind == "question" and frame.get("focus") == "thing"
            and rel.get("oblique") is not None):
        oblique = str(rel["oblique"].get("surface") or "").strip(".,;:?!").lower()
        oi = next((i for i, e in enumerate(elements)
                   if str(e.get("surface") or "").strip(".,;:?!").lower() == oblique), None)
        if oi is not None:
            prep = next((e for e in reversed(elements[:oi])
                         if e.get("pos") in {"preposition", "postposition"}), None)
            if prep is not None:
                role = _prep_roles.preposition_role(
                    str(prep.get("surface") or "").strip(".,;:?!").lower(), "en")
                # ``preposition_role`` is the fine-grained VerbNet-derived
                # lookup.  Spatial membership is a separate, coarse role
                # faculty and must remain authoritative when the generated
                # cache has no entry for a spatial preposition (for example
                # ``beyond``).  Otherwise the held-answer fast path can
                # mistake an unobserved scene question for a lexical topic.
                if role == "location" or _prep_roles.is_spatial(
                        str(prep.get("surface") or "").strip(".,;:?!"), "en"):
                    evidence["world_dependency"] = "spatial_relation"
                    evidence["world_support"] = (
                        "available" if getattr(agent, "_conv_scene", None) is not None
                        else "missing")

    # Distance/extent questions may be represented as a manner focus rather
    # than an oblique PP (for example, "How far is the valley?").  They still
    # depend on an attached world.  Emit only the neutral dependency category;
    # cognition decides whether the scene supplies support.
    if kind == "question" and frame.get("focus") == "manner":
        extent_terms = {"far", "near", "distance", "close", "closer", "farthest"}
        if any(str(e.get("surface") or "").strip(".,;:?!").lower() in extent_terms
               for e in elements):
            evidence["world_dependency"] = "spatial_relation"
            evidence["world_support"] = (
                "available" if getattr(agent, "_conv_scene", None) is not None
                else "missing")

    # A selection focus with an unresolved nominal/verb residual is a repair
    # request, even when a second-person subject is present.  The subject's
    # person is not evidence that the question is about the agent.
    if (kind == "question" and frame.get("focus") == "selection"
            and rel.get("subject", {}).get("role") == "function"
            and rel.get("object") is None and rel.get("oblique") is None
            and frame.get("gaps")):
        focus = next((str(e.get("surface") or "").strip(".,;:?!")
                      for e in elements if e.get("role") == "content"
                      and e.get("pos") == "noun"), None)
        evidence.update({"repair_evidence": "unresolved_selection",
                         "referent_status": "unresolved",
                         "repair_focus": focus or "selection"})

    # Demonstrative determiners create deictic reference evidence.  The
    # object noun may itself be a held Concept, but that does not resolve the
    # discourse referent unless graph state supplies the binding.
    if kind == "instruction" and rel.get("object") is not None:
        obj = str(rel["object"].get("surface") or "").strip(".,;:?!").lower()
        oi = next((i for i, e in enumerate(elements)
                   if str(e.get("surface") or "").strip(".,;:?!").lower() == obj), None)
        if oi is not None:
            det = next((e for e in reversed(elements[:oi])
                        if e.get("pos") == "determiner"), None)
            if det is not None and str(det.get("surface") or "").lower() in _DEICTIC_DETERMINERS:
                resolved = _graph_referent_available(agent, obj)
                evidence.update({"deictic_reference": True,
                                 "referent_status": "supported" if resolved else "unresolved",
                                 "referent_target": obj})

    # A declarative self-report can be a knowledge-deficit repair event. The
    # adapter exposes this only when its graph-resident predicate concept has
    # semantic evidence that the state requires relief; cognition does not
    # match the literal predicate or infer repair from wording alone.
    if (kind == "statement"
            and isinstance(rel.get("subject"), dict)
            and rel.get("subject", {}).get("pos") == "pronoun"
            and isinstance(rel.get("predicate"), dict)
            and rel.get("predicate", {}).get("role") == "content"
            and rel.get("object") is not None):
        predicate = str(rel["predicate"].get("surface") or "").strip(".,;:?!").lower()
        for node in getattr(agent, "s", agent).nodes("Concept"):
            attrs = getattr(agent, "s", agent).node(node)["attrs"]
            if str(attrs.get("name") or "").lower() != predicate:
                continue
            definition = str(attrs.get("definition") or "").lower()
            role = str(attrs.get("semantic_role") or "").lower()
            if role in {"knowledge_deficit", "epistemic_need"} \
                    or "requiring relief" in definition:
                evidence.update({
                    "repair_evidence": "knowledge_deficit",
                    "repair_focus": str(rel["object"].get("surface") or "")
                    .strip(".,;:?!"),
                })
                break

    # A modal/action frame is authority evidence emitted by the language
    # adapter. It is structural (typed heads plus an actor slot), not a list
    # of English permission words; cognition still requires a graph-resident
    # authority decision before release.
    content = [e for e in elements if e.get("role") == "content"]
    modal_semantic = False
    if content:
        modal_name = str(content[0].get("surface") or "").strip(
            ".,;:?!").lower()
        for node in getattr(agent, "s", agent).nodes("Concept"):
            attrs = getattr(agent, "s", agent).node(node)["attrs"]
            if str(attrs.get("name") or "").lower() != modal_name:
                continue
            definition = str(attrs.get("definition") or "").lower()
            role = str(attrs.get("semantic_role") or attrs.get("modality") or "").lower()
            if (role in {"permission", "permission_modality", "ability_permission"}
                    or ("permission" in definition and "modal" in definition)):
                modal_semantic = True
                break
    if (kind == "question" and modal_semantic and len(content) >= 2
            and any(e.get("role") == "function" and e.get("pos") == "pronoun"
                    for e in elements)
            and content[0].get("pos") == "verb"
            and content[1].get("pos") == "verb"):
        evidence.update({
            "authority_request": True,
            "modality_evidence": "typed_modal_action_frame",
            "action_predicate": str(content[1].get("surface") or "").strip(
                ".,;:?!"),
        })

    # Anaphoric question frames can carry a resolved discourse binding even
    # when no external topic answer is held.  The binding is accepted only
    # from graph-resident discourse state, never from the pronoun itself.
    relation_slots = (rel.get("subject"), rel.get("object"),
                      rel.get("oblique"))
    if (kind == "question"
            and any(isinstance(slot, dict) and slot.get("pos") == "pronoun"
                    for slot in relation_slots)
            and _graph_discourse_binding_available(agent)):
        evidence.update({
            "resolved_reference_status": "supported",
            "resolved_reference_evidence": (
                "CommunicationInterpretation -> CurrentTopic.name + "
                "DiscourseReferent.concept"),
        })

    # Directive structure is language-adapter evidence, not a cognition
    # ontology or an English command list.  The adapter's held verb-head
    # faculty identifies action-headed spans; cognition receives only the
    # resulting neutral predicates, target, compound membership, and whether
    # a typed temporal focus defers execution.
    if kind == "instruction":
        first = elements[0] if elements else {}
        content_indices = [i for i, e in enumerate(elements)
                           if e.get("role") == "content"]
        predicate_indices = []
        if content_indices:
            if first.get("role") == "focus":
                # A typed temporal focus introduces the action clause; skip
                # its descriptive complement and select the next supported
                # action head after that boundary.
                predicate_indices.append(next(
                    (i for i in content_indices[1:]
                     if elements[i].get("pos") != "adj"
                     and _ir.is_verb_headed(str(elements[i].get("surface") or "")
                                            .strip(".,;:?!"))),
                    content_indices[0]))
            else:
                predicate_indices.append(content_indices[0])
            # Coordinate clause boundaries are structural evidence. The first
            # content element after a conjunction is another action head;
            # following content remains that clause's target.
            for i, element in enumerate(elements):
                if element.get("pos") == "conjunction":
                    following = next((j for j in content_indices if j > i), None)
                    if following is not None and _ir.is_verb_headed(
                            str(elements[following].get("surface") or "")
                            .strip(".,;:?!")):
                        predicate_indices.append(following)
        predicate_indices = list(dict.fromkeys(predicate_indices))
        if predicate_indices:
            predicates = [str(elements[i].get("surface") or "").strip(".,;:?!")
                          for i in predicate_indices]
            evidence["action_predicates"] = predicates
            evidence["action_predicate"] = predicates[0]
            first_index = predicate_indices[0]
            target_element = next(
                (e for e in elements[first_index + 1:]
                 if (e.get("role") == "content"
                     or (e.get("role") == "function"
                         and e.get("pos") == "pronoun"))
                 and str(e.get("surface") or "").strip(".,;:?!")),
                None)
            if target_element is not None:
                target = str(target_element.get("surface") or "").strip(
                    ".,;:?!")
                evidence["action_target"] = target
                if target_element.get("pos") == "pronoun":
                    # A pronoun is a typed reference expression, not a
                    # lexical action object.  Preserve its resolution state
                    # for cognition; do not bind it to the next adverb or
                    # invent a referent from surface order.
                    resolved = _graph_discourse_binding_available(agent)
                    evidence.update({
                        "anaphoric_reference": True,
                        "referent_status": "supported" if resolved else "unresolved",
                        "repair_focus": target,
                    })
            if len(predicates) > 1:
                evidence["action_sequence"] = predicates
            if first.get("role") == "focus" and first.get("pos") in {
                    "time", "condition", "temporal"}:
                evidence["deferred_condition"] = True
                evidence["condition_evidence"] = "typed_temporal_focus"
            # The language adapter exposes the existing self-account faculty
            # when this typed action frame is an account request addressed to
            # the agent. This is evidence transport, not a new grounding
            # decision or a reply heuristic.
            first_predicate = str(predicates[0] if predicates else "").lower()
            self_addressed = any(
                str(element.get("surface") or "").lower() in _SELF_CUES
                for element in elements
            )
            if first_predicate in _ACCOUNT_VERBS and self_addressed:
                evidence["account_request"] = "selected_self_account_faculty"
    return evidence


def _strip_politeness(agent: Any, text: str) -> str:
    """Strip leading politeness/discourse markers ("Pray,", "kindly", "prithee",
    "please") so the ornate question/instruction underneath parses as itself.
    The leading marker is identified by RECOGNITION (the first recognised word,
    not a regex): recognise the remaining text, and while its FIRST recognised
    word is a politeness marker with more content behind it, slice past that
    marker's occurrence (and a following comma). Returns the original text
    unchanged when there is nothing to strip."""
    base = (text or "").lstrip()
    s = base
    changed = False
    while True:
        words = _recognise_words(agent, s)
        if len(words) < 2 or words[0] not in _POLITENESS_MARKERS:
            break
        idx = s.lower().find(words[0])
        if idx < 0:
            break
        after = s[idx + len(words[0]):].lstrip()
        if after and after[0] == ",":
            after = after[1:].lstrip()
        if not after:
            break
        s = after
        changed = True
    return s if changed else text


# ---------------------------------------------------------------------------
# WORD READING = SEGMENTATION-BY-RECOGNITION (cognition, not I/O). The ONLY I/O
# is the raw characters; WORD boundaries EMERGE by recognising the char stream
# against the agent's lexicon codebook (instruction_reading's decoder), exactly
# as the meta-layer's instruction comprehension does. Whitespace is a WEAK cue —
# a run-together / mis-spaced input ("whatareyou") still segments to the right
# words, where a `.split()` would mis-tokenise. READ-ONLY: it gathers the
# agent's lexicon (a graph read) and decodes the characters WITHOUT minting any
# Word/Char node into the live agent graph (comprehend_text stays side-effect
# free), reusing instruction_reading.gather_lexicon + its lattice decoder as-is.
# ---------------------------------------------------------------------------

def _ws_tokens(s: str) -> list[str]:
    """The whitespace-delimited tokens of `s` by a manual char scan (NO `.split()` —
    the recogniser stays scan/recognition-based, audited clean). Whitespace is only
    a weak cue used to OFFER dictionary-word candidates, never a hard delimiter."""
    out: list[str] = []
    cur: list[str] = []
    for ch in s:
        if ch.isspace():
            if cur:
                out.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


_DICT_WORD_CACHE: dict[str, bool] = {}


def _is_dictionary_word(token: str) -> bool:
    """True iff `token` is a REAL word (a held WordNet lemma) — the signal that a
    space-delimited token should stay WHOLE rather than be shredded into shorter
    known fragments. Cached (WordNet is deterministic). A run-together of known words
    ('areyou') is NOT a lemma, so recognition still splits it."""
    t = token.lower()
    hit = _DICT_WORD_CACHE.get(t)
    if hit is None:
        try:
            from nltk.corpus import wordnet as wn
            hit = bool(wn.synsets(t))
        except Exception:
            hit = False
        _DICT_WORD_CACHE[t] = hit
    return hit


def _recognise_regions(agent: Any, text: str) -> list[list[str]]:
    """Recognise `text` into punctuation-delimited regions of recognised words.
    Punctuation (`_ir._PUNCT`) is a hard mark that ends a region (mirrors the
    agent's own instruction segmenter); within a region the words emerge by
    lexicon-lattice recognition over the characters (whitespace a weak cue).
    Surrounding quote/paren marks are trimmed from each recognised word (the
    same trim the old whitespace tokeniser applied)."""
    if not text:
        return []
    try:
        lex = _ir.gather_lexicon(agent)
    except Exception:
        lex = set(_ir._CLOSED_CLASS)
    regions: list[list[str]] = []
    region: list[str] = []

    def flush() -> None:
        reg = "".join(region)
        region.clear()
        if not reg.strip():
            return
        # Whitespace is a WEAK cue, but a space-delimited token that is a REAL
        # DICTIONARY WORD is one: seed the decode lexicon with the region's own
        # space-delimited tokens that WordNet recognises, so a real content word
        # absent from the agent's lexicon ('weather', 'pebbles', 'pitcher') stays
        # WHOLE instead of being shredded into shorter known fragments ('weather' ->
        # 'we'+'at'+'her'). Gated on dictionary-hood, NOT on mere spacing: a
        # run-together of known words ('areyou') is NOT a dictionary word, so it is
        # still lattice-decoded to [are, you] — recognition still overrides bad
        # spacing. Tokens are read by a char scan (no whitespace `.split()`).
        local = set(lex)
        for tok in _ws_tokens(reg):
            t = tok.strip("\"'()[]{}.,!?;:").lower()
            if t and t.isalpha() and _is_dictionary_word(t):
                local.add(t)
        decoded = _ir._lattice_decode(reg, local)
        words = decoded[0] if isinstance(decoded, tuple) else decoded
        cleaned = [w.strip("\"'()") for w in words]
        regions.append([w for w in cleaned if w])

    for ch in text:
        if ch in _ir._PUNCT:
            flush()
        else:
            region.append(ch)
    flush()
    return regions


def _recognise_words(agent: Any, text: str) -> list[str]:
    """The recognised words of `text`, flattened across regions — the
    recognition-based replacement for a whitespace `.split()` tokeniser."""
    return [w for reg in _recognise_regions(agent, text) for w in reg]


def _paren_regions(agent: Any, text: str) -> Optional[list]:
    """Mechanical I/O, additive: split `text` at its FIRST balanced parenthetical
    span '( ... )' into three recognised-word regions [before, inside, after].
    Parens are deliberately NOT in `_ir._PUNCT` (so `_recognise_words`/
    `_recognise_regions` — the byte-parity-critical tokenizer every frozen
    fixture depends on — are completely untouched by this function; it is a
    wholly separate, additive reader). Each segment is word-recognised by the
    EXISTING `_recognise_words` (reused unmodified, not reimplemented). Returns
    None when `text` carries no balanced paren pair. Pure boundary
    SEGMENTATION — the same status as `_recognise_regions`'s own comma-flush
    boundary, generalised to a paren pair; no claim about what the parenthetical
    MEANS is made here (that is `reading_collapse`'s ShapeDecode call, over the
    taught `parenthetical_definition` construction)."""
    i = text.find("(")
    if i < 0:
        return None
    j = text.find(")", i + 1)
    if j < 0:
        return None
    before, inside, after = text[:i], text[i + 1:j], text[j + 1:]
    return [_recognise_words(agent, before), _recognise_words(agent, inside),
            _recognise_words(agent, after)]


# ---------------------------------------------------------------------------
# PREDICTION-GUIDED CHARACTER-SUBSTITUTION TOLERANCE — the AbS bias one grain
# DOWN, at the CHARACTER level. Bottom-up recognition disambiguates a MISSING
# SPACE (the lattice re-segments run-together known words), but NOT a substituted
# character ('b1rd' for 'bird'): '1' is not in any lexicon word, so the token
# stays OOV. When the reader's writer-model has PREDICTED the word, the noisy
# token need only be CONSISTENT with that prediction at the character grain — the
# prediction is the codebook, the noisy chars are decoded against it, and the
# per-position mismatch IS the AbS residual one grain down. NOT a hardcoded typo
# table: the tolerated words are exactly the model's PREDICTIONS, and the
# consistency is a computed per-position char agreement (decided by the Rust
# evaluator over scratch Char nodes, the _scratch_words/_holds discipline).
# ---------------------------------------------------------------------------
def _char_consistency(a: str, b: str) -> Optional[int]:
    """Number of CHARACTER positions at which equal-length strings `a` and `b`
    AGREE (else None — character SUBSTITUTION preserves length). The per-position
    agreement is decided by the Rust evaluator over scratch Char nodes (an Eq Term
    per position — the SAME scratch-evaluate discipline `_match_self_identity`
    uses for question shapes), so the consistency DECISION is graph-native, not a
    Python typo table. `len(a) - agree` is the char-grain AbS residual."""
    if len(a) != len(b):
        return None
    s = None
    try:
        from substrate_rs import _native
        s = _native.Substrate()
    except Exception:
        s = None
    term = {"type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "char"},
            "b": {"type": "Attr", "node": {"type": "Var", "name": "y"}, "key": "char"}}
    agree = 0
    for ca, cb in zip(a, b):
        if s is not None:
            try:
                nx = s.add_node("Char", {"char": ca})
                ny = s.add_node("Char", {"char": cb})
                if bool(s.evaluate(term, {"x": nx, "y": ny})):
                    agree += 1
                continue
            except Exception:
                s = None                     # fall through to the direct compare
        if ca == cb:
            agree += 1
    return agree


def char_sub_recover(token: str, predicted_words: list[str]) -> Optional[str]:
    """Given an OOV `token` that may carry character-SUBSTITUTION noise and the
    writer model's PREDICTED words, return the predicted word the token is
    CONSISTENT with — same length, char-substitution residual within tolerance
    (`max(1, len//3)`) and at least one substitution — else None. The prediction
    proposes the word; the noisy token need only CONFIRM it at the character grain,
    not be identified bottom-up. Ties break to the SMALLEST residual, then the
    first-predicted (deterministic). Bottom-up (no prediction) cannot do this:
    there is no codebook word to be consistent WITH."""
    t = (token or "").lower().strip("\"'()[]{}.,!?;:")
    if not t:
        return None
    best, best_res = None, None
    for p in predicted_words:
        p = (p or "").lower().strip("\"'()[]{}.,!?;:")
        if not p or len(p) != len(t) or p == t:
            continue
        agree = _char_consistency(t, p)
        if agree is None:
            continue
        res = len(t) - agree
        tol = max(1, len(t) // 3)
        if 1 <= res <= tol and (best_res is None or res < best_res):
            best, best_res = p, res
    return best


# --- GRAPH-NATIVE question/intent shape matches over the recognised words. A
# token-sequence intent (a self-identity question) is COGNITION, not a regex:
# it is an In/Eq/And Term the Rust evaluator runs over scratch Word nodes carrying
# the recognised `text` attr — the exact discipline instruction_reading uses for
# connective recognition (`word_in` = In(Attr(w,"text"), options)). ---
_WHO_WHAT = ["what", "who"]
_ARE_ART = ["are", "art"]
_YOU_THOU = ["you", "thou", "thee"]
_KIND_NOUNS = ["sort", "kind", "manner", "type"]
# wh-leads that make a region a wh-question (used to keep the POLAR
# self-classification fallback polar-only).
_WH_WORDS = frozenset({"what", "who", "which", "how", "why", "when", "where", "whom"})


def _V(n: str) -> dict: return {"type": "Var", "name": n}
def _Attr(node: dict, k: str) -> dict: return {"type": "Attr", "node": node, "key": k}
def _In(var: str, opts) -> dict:
    return {"type": "In", "member": _Attr(_V(var), "text"),
            "container": {"type": "Lit", "value": list(opts)}}
def _Eq(var: str, val) -> dict:
    return {"type": "Eq", "a": _Attr(_V(var), "text"), "b": {"type": "Lit", "value": val}}
def _And(items) -> dict: return {"type": "And", "items": list(items)}


def _scratch_words(words: list[str]):
    """Mint each recognised word as a scratch Word node (a throwaway native
    substrate — never the agent's graph) so the In/Eq/And question-shape Terms can
    be evaluated over its `text` attr, the same scratch-evaluate discipline
    instruction_reading.is_verb_headed uses."""
    try:
        from substrate_rs import _native
        s = _native.Substrate()
        return s, [s.add_node("Word", {"text": w}) for w in words]
    except Exception:
        return None, None


def _detect_satisfiable(agent: Any, text: str) -> Optional[str]:
    """A leading enumerate verb ("Name"/"List one of your rules") over held
    data + a self-possessive + a held-data noun -> the target faculty key
    ("rules" / "organisation"). None when it is not such an instruction."""
    recognised = [w.lower() for w in _recognise_words(agent, text)]
    surface = [w.lower().strip(" ,.;:?!") for w in _ws_tokens(text)]
    words = surface if surface else recognised
    if not words:
        return None
    enum_i = 0 if words and words[0] in _ENUMERATE_VERBS else (
        2 if len(words) > 2 and words[0] in _MODAL_REQUEST_PREFIXES
        and words[1] in _YOU_THOU and words[2] in _ENUMERATE_VERBS else None)
    if enum_i is None:
        return None
    if not any(w in ("your", "yours", "my") for w in words[enum_i + 1:]):
        return None
    for w in words[enum_i + 1:]:
        tgt = _SATISFIABLE_TARGET.get(w)
        if tgt:
            return tgt
    return None


def _is_perception_request(agent: Any, text: str) -> bool:
    """A leading account verb ("describe"/"report"/...) + a perception cue
    ("perceive"/"see"/...) -> a request to report the perceived world."""
    words = _recognise_words(agent, text)
    if not words or words[0] not in _ACCOUNT_VERBS:
        return False
    return any(w in _PERCEPTION_CUES for w in words[1:])


def _ends_question(text: str) -> bool:
    return (text or "").strip().endswith("?")


# SELF-IDENTITY question shapes — "what/who are you", "what sort/kind/manner/type
# of thing are you". These are REFLEXIVE identity questions the agent answers from
# its self_identity faculty. Without this intercept, the bare "What are you?" fast-
# paths through the construction table to know('you') ("I don't know you") and
# "what SORT of thing are you?" grounds to the sorting_principle faculty (a raw
# diagnostic dump). The two shapes are narrow (they require "are you" to follow
# the wh directly, or a sort/kind/manner/type nominal) so "what SHAPE are you?" /
# "what are your limits?" keep their existing self_shape / frontier routing.
#
# Recognising the shape is COGNITION, not regex: the recognised words become
# scratch Word nodes and the shape is an In/Eq/And Term the Rust evaluator runs
# over them (per punctuation-delimited region, so a comma/`?` between the tokens
# breaks the adjacency exactly as `\s+`-only regex did). Two shapes:
#   (1) w[i] In {what,who}  And  w[i+1] In {are,art}  And  w[i+2] In {you,thou,thee}
#   (2) w[i]=="what"  And  w[i+1] In {sort,kind,manner,type}  And  w[i+2]=="of",
#       with an {are,art}+{you,thou,thee} tail 0-or-1 word later.


def _holds(s, term, binding, fallback: bool) -> bool:
    """Evaluate a graph shape Term over scratch Word nodes (the DECISION is the
    Rust evaluator's, the In/Eq/And path); `fallback` is used only if no native
    substrate is available."""
    if s is None:
        return fallback
    try:
        return bool(s.evaluate(term, binding))
    except Exception:
        return fallback


def _match_self_identity(words: list[str]) -> bool:
    n = len(words)
    if n < 3:
        return False
    s, nodes = _scratch_words(words)

    def nid(i):
        return nodes[i] if nodes is not None else None

    # (1) (what|who) (are|art) (you|thou|thee) — adjacent, and REGION-FINAL:
    # a bare identity question ends at the self-pronoun ("what are you?");
    # a trailing word makes it a progressive/wh-object question ("what are
    # you working on?") that must fall through to the meta-target lexicon,
    # not the identity intercept. Same narrow-shape discipline as the
    # docstring above promises.
    p1 = _And([_In("w0", _WHO_WHAT), _In("w1", _ARE_ART), _In("w2", _YOU_THOU)])
    for i in range(n - 2):
        if i + 2 != n - 1:
            continue
        fb = (words[i] in _WHO_WHAT and words[i + 1] in _ARE_ART
              and words[i + 2] in _YOU_THOU)
        if _holds(s, p1, {"w0": nid(i), "w1": nid(i + 1), "w2": nid(i + 2)}, fb):
            return True

    # (2) what (sort|kind|manner|type) of [word]? (are|art) (you|thou|thee).
    head = [_Eq("w0", "what"), _In("w1", _KIND_NOUNS), _Eq("w2", "of")]
    for i in range(n - 2):
        for gap in (0, 1):
            a, y = i + 3 + gap, i + 4 + gap
            if y >= n:
                continue
            term = _And(head + [_In("wa", _ARE_ART), _In("wy", _YOU_THOU)])
            fb = (words[i] == "what" and words[i + 1] in _KIND_NOUNS
                  and words[i + 2] == "of" and words[a] in _ARE_ART
                  and words[y] in _YOU_THOU)
            binding = {"w0": nid(i), "w1": nid(i + 1), "w2": nid(i + 2),
                       "wa": nid(a), "wy": nid(y)}
            if _holds(s, term, binding, fb):
                return True
    return False


def _detect_self_identity(agent: Any, text: str) -> bool:
    """A reflexive SELF-IDENTITY question ('what/who are you', 'what sort of thing
    are you') -> route to the self_identity faculty. Recognised words + a
    graph In/Eq/And shape match (per region), not a regex."""
    return any(_match_self_identity(reg) for reg in _recognise_regions(agent, text))


def _detect_self_kind(agent: Any, text: str) -> dict | None:
    """A copular polar self-CLASSIFICATION ('are you an LLM?') -> route to the
    self_kind faculty. Mechanical relation read from the parser frame; a narrow
    word-shape fallback when the frame is unavailable."""
    try:
        frame = _cg.parse_with_gaps(text, agent)
    except Exception:
        frame = None
    rel = {}
    if frame:
        try:
            rel = _cg.compose_relation(frame) or {}
        except Exception:
            rel = {}
    if rel.get("focus") == "polar":
        subj = str((rel.get("subject") or {}).get("surface", "")).lower().strip(",.;:?!")
        pred = rel.get("predicate") or {}
        obj = rel.get("object")
        if (subj in _SELF_CUES and pred.get("pos") == "copula" and obj is not None):
            kind = str(obj.get("surface", "")).strip(",.;:?!")
            if kind and kind.lower() not in _SELF_CUES:
                return {"kind": kind, "relation": rel, "frame": frame}
    # Fallback: (are|art) (you|thou|thee) (a|an)? <kind> — POLAR only, per this
    # intercept's documented intent: a region led by a wh word ("what
    # experiments are you running?") is a wh-question, not a copular
    # self-classification, and must fall through to the meta-target lexicon.
    for reg in _recognise_regions(agent, text):
        words = [w.lower().strip(",.;:?!") for w in reg]
        if words and words[0] in _WH_WORDS:
            continue
        for i in range(len(words) - 2):
            if words[i] not in _ARE_ART or words[i + 1] not in _YOU_THOU:
                continue
            j = i + 2
            if j < len(words) and words[j] in ("a", "an", "the"):
                j += 1
            if j < len(words) and words[j] not in _SELF_CUES:
                return {"kind": reg[j].strip(",.;:?!"), "relation": rel, "frame": frame}
    return None


def _is_name_inquiry(text: str) -> bool:
    """A question ABOUT the agent's own NAME (a genuine name reference in the
    interlocutor's text) -> the own-name (Carroll) explanation. Delegates to the
    sense-of-reference trigger gate so there is one source of truth; returns False
    if that faculty is unavailable (the general path then handles the text)."""
    try:
        from domains import sense_of_reference as _sor
        return bool(_sor.is_name_inquiry(text))
    except Exception:
        return False


def _detect_self_process(substrate: Any, text: str) -> Optional[str]:
    """A reflexive MANNER process-question ('how do you <verb>' / 'how does a
    world attach to you') the agent HOLDS a true self-account for -> the canonical
    process name of the matching held SelfProcess node, else None. This is the
    OPERATIONAL-INTROSPECTION boundary classifier: it reads whether the agent
    genuinely holds a self-account (`self_model.find_self_process`, a real graph
    read) for the process the question names, and fires ONLY then — so it can run
    BEFORE the held construction table (which otherwise grounds 'how do you
    perceive?' to the self_design machinery dump) and reach the true self-account,
    while a process the agent has no account for (dream/sleep/...) falls straight
    through to the honest floor. Gated to a manner NON-structure reflexive question
    so a genuine self-STRUCTURE question ('how are you organised/composed?') keeps
    its self_organisation routing untouched. Cheap pre-filter (a 'how' + self-cue
    surface check) avoids parsing every input twice."""
    toks = set(_recognise_words(substrate, text))
    if "how" not in toks or not (toks & _SELF_CUES):
        return None
    try:
        frame = _cg.parse_with_gaps(text, substrate)
    except Exception:
        return None
    if frame.get("focus") != "manner" or _asks_self_structure(frame):
        return None
    if not _has_self_cue(frame):
        return None
    try:
        return _self_model.find_self_process(substrate, _all_words(frame))
    except Exception:
        return None


def comprehend_text(agent: Any, text: str, *, kind: Optional[str] = None) -> Comprehension:
    """Comprehend ARBITRARY text. `kind`, when given, is the speech-act KIND
    the GRAPH already decided (converse() runs the seeded speech_act_classify
    rules over the live inbound Message and passes the minted sak_kind back —
    a mechanical read). When absent (direct callers), the SAME seed rules
    decide on a scratch Message (`_classify_kind_rules`); the Python ladder
    `_classify_kind` remains only as the documented no-native fallback.

    Before the held construction table, four
    ROBUST-ROUTING intercepts kill the "understood" catch-all and reach the
    real intent (all reasoned over GROUNDED signals — grammar, self-model,
    morphology — never a per-word table):

      * POLITENESS — strip leading "Pray,"/"kindly"/... so the ornate question
        underneath parses as itself (not a bogus "Pray the nature" instruction);
      * COINAGE -> WORDPLAY — an OOV morphologically-analysable / portmanteau
        token (the jabberwock's namesake faculty) routes to a playful,
        shape-inferred reply, distinct from a genuine unknown (which still
        asks back / answers normally);
      * SATISFIABLE — "Name one of your rules" is answered from held data;
      * HONEST NO-WORLD — "Describe what you perceive" with no scene attached
        hits the honest "no world to perceive", never "understood".

    Then the held table (fast path, regression-safe); then the general gap-as-
    part-of-speech parser + relation composer. Never raises on ordinary input."""
    substrate = getattr(agent, "s", agent)
    original = text or ""
    # POLITENESS — strip leading discourse markers, then parse the remainder.
    text = _strip_politeness(agent, original)

    # NAME-INQUIRY — a question ABOUT the agent's own name ("why are you named X",
    # "whence comes your name", "are you the Jabberwock") -> the name-as-reference
    # (Carroll) explanation via the sense-of-reference own-name path (handled in
    # converse's reference dispatch). Gated on a GENUINE name reference in the
    # interlocutor's text (`sense_of_reference.is_name_inquiry`), so a plain self-
    # identity question / farewell / greeting / thanks never lands here. This makes
    # the turn NON-fastpath so the reference dispatch (not the table) resolves it.
    if _is_name_inquiry(text):
        return Comprehension(
            raw=original, kind="question", reflexive=True, focus="thing",
            dispatch={"path": "own_name"}, intent="own_name",
            note="a question about the agent's own name -> the name-as-reference (Carroll) explanation")

    # SELF-IDENTITY — "what/who are you", "what sort of thing are you" -> the
    # self_identity faculty (a real self answer), NOT the table's know('you')
    # ("I don't know you") and NOT the sorting_principle diagnostic dump. Non-
    # fastpath meta dispatch; answer_question consumes it via the same reflect()
    # backend as the wh-default reflexive path.
    if _detect_self_identity(agent, text):
        return Comprehension(
            raw=original, kind="question", reflexive=True, focus="thing",
            dispatch={"path": "meta", "meta_target": "self_identity", "meta_arg": None,
                      "strategy": "self_identity_intercept"},
            intent="ask_self:self_identity",
            note="a self-identity question routed to the self_identity faculty "
                 "(not know('you') / not a raw principles dump)")

    # SELF-KIND — "are you an LLM?", "are you a chatbot?" -> copular polar
    # self-CLASSIFICATION. NOT answer_topic (that wrongly Wikipedia-grounds the
    # kind noun, e.g. LLM -> LLM01 military hardware) and NOT self_identity.
    sk = _detect_self_kind(agent, text)
    if sk is not None:
        return Comprehension(
            raw=original, kind="question", reflexive=True, focus="polar",
            relation=sk.get("relation"),
            frame=sk.get("frame"),
            dispatch={"path": "meta", "meta_target": "self_kind", "meta_arg": sk["kind"],
                      "strategy": "self_kind_intercept"},
            intent=f"ask_self:kind({sk['kind']!r})",
            note="a copular self-classification question routed to self_kind "
                 "(not answer_topic / not Wikipedia grounding of the kind noun)")

    # OPERATIONAL SELF-INTROSPECTION — a reflexive 'how do you <verb>' process
    # question the agent HOLDS a true self-account for (a taught SelfProcess:
    # learning=collapse, perceiving=sd-decode, world-attachment=adapter-ingest).
    # Runs BEFORE the held table because the table grounds e.g. 'how do you
    # perceive?' to the self_design MACHINERY DUMP; the held self-account is the
    # truthful, substantive answer. Fires ONLY when the account is genuinely held
    # (find_self_process reads the graph) — a process with no held account
    # (dream/sleep) falls through to the honest floor unchanged.
    proc = _detect_self_process(substrate, text)
    if proc is not None:
        return Comprehension(
            raw=original, kind="question", reflexive=True, focus="manner",
            dispatch={"path": "meta", "meta_target": "self_process", "meta_arg": proc,
                      "strategy": "self_process_grounded"},
            intent="ask_self:self_process",
            note="an operational self-process question answered from the agent's "
                 "held self-account (taught from the real architecture, not fabricated)")

    # COINAGE -> WORDPLAY (before the table: the table mis-grounds a coinage as a
    # KNOW/meta target). A genuine unknown / proper noun returns None here and
    # falls through to the normal ask-back / answer path.
    try:
        coin = _wp.find_coinage(original)
    except Exception:
        coin = None
    if coin is not None:
        return Comprehension(
            raw=original, kind=("question" if _ends_question(original) else "statement"),
            dispatch={"path": "wordplay", "coinage": coin.get("word"), "analysis": coin},
            intent=f"wordplay:{coin.get('word')}",
            note="a playful coinage engaged by the wordplay faculty (shape-inferred, flagged as inference)")

    # SATISFIABLE — an imperative to enumerate held data, answered from the graph.
    sat = _detect_satisfiable(agent, text)
    if sat is not None:
        return Comprehension(
            raw=original, kind="question",
            dispatch={"path": "satisfiable", "target": sat},
            intent=f"satisfiable:{sat}",
            note="an instruction satisfiable from my held data (answered, not acknowledged)")

    # HONEST NO-WORLD — a perception request with no scene attached.
    if _is_perception_request(agent, text) and getattr(agent, "_conv_scene", None) is None:
        _pw = _recognise_words(agent, text)
        pred = _pw[0] if _pw else None
        return Comprehension(
            raw=original, kind="instruction",
            dispatch={"path": "honest_no_world", "predicate": pred},
            intent="honest_no_world",
            note="a perception request but no world/scene is attached (honest, not 'understood')")

    spec = None
    try:
        spec = _cq.comprehend(text)
    except Exception:
        spec = None
    if spec is not None and getattr(spec, "grounded", False):
        # The held know-table can ground a lexical topic while the adapter's
        # semantic frame still says that the requested fact depends on an
        # unobserved spatial scene. Preserve legitimate table/meta routes; only
        # withdraw the external route when the world dependency is explicit and
        # graph state lacks the required scene.
        table_frame = _cg.parse_with_gaps(text, substrate)
        table_rel = _cg.compose_relation(table_frame)
        table_evidence = _language_adapter_evidence(
            agent, table_frame, table_rel, kind="question")
        table_dispatch = {"path": "table", "spec": spec, "table_kind": spec.kind}
        if (table_evidence.get("world_dependency") == "spatial_relation"
                and table_evidence.get("world_support") == "missing"):
            table_dispatch.update({
                "path": "frontier",
                "reason": "spatial world dependency lacks an attached scene",
                "language_evidence": table_evidence,
            })
        elif table_evidence:
            table_dispatch["language_evidence"] = table_evidence
        return Comprehension(
            raw=text, kind="question", fastpath=True, table_spec=spec,
            dispatch=table_dispatch,
            intent=("ask_world:unresolved"
                    if table_dispatch.get("path") == "frontier"
                    else f"table:{spec.kind}"),
            note="comprehended by the existing construction table (fast path)")

    frame = _cg.parse_with_gaps(text, substrate)
    gaps = frame.get("gaps", [])
    # KIND is the GRAPH'S decision (Wave 4): the caller passed the live
    # Message's rule-minted sak_kind, or the same seed rules decide on a
    # scratch Message here. The Python ladder runs ONLY when no engine is
    # available (the `_holds` fallback discipline).
    if kind not in ("question", "instruction", "statement"):
        signals = _signals_of(text, frame)
        # Keep the established one-argument fallback seam intact for direct
        # callers and tests that replace the native classifier.  A receipt is
        # meaningful only when this is a live adapter call with a graph sink.
        if (agent is not None and hasattr(agent, "s")
                and hasattr(agent, "agent")):
            kind = _classify_kind_rules(signals, receipt_sink=agent)
        else:
            kind = _classify_kind_rules(signals)
    if kind == "statement" and first_imperative_evidence(
            agent, original, first_role=_first_element(frame).get("role")
            if _first_element(frame) else None,
            first_pos=_first_element(frame).get("pos")
            if _first_element(frame) else None):
        # Canonical comprehension may resolve a pragmatic polite imperative
        # even when the native speech-act classifier conservatively retained a
        # statement reading. This is deliberately after native evidence is
        # recorded, so the disagreement remains auditable.
        kind = "instruction"
    if kind == "statement":
        surface = [w.lower().strip(" ,.;:?!") for w in _ws_tokens(text)]
        if surface and surface[0] in _ACCOUNT_VERBS:
            # Canonical comprehension preserves the reporting/account force
            # even when the POS faculty failed to recognize the leading verb.
            # The graph arbitration layer still decides whether the account is
            # informational or actionable from the resulting predicate.
            kind = "instruction"
    if kind is None:
        kind = _classify_kind(text, frame)
    comp = Comprehension(raw=text, kind=kind, focus=frame.get("focus"),
                          frame=frame, gaps=gaps)

    if not frame.get("elements"):
        # empty / unparseable input (no tokens at all, e.g. "", "   ", "?"
        # alone) — `compose_relation` is documented single-clause and hits a
        # latent bug on a genuinely EMPTY element list (construction_grammar.py
        # is not in this task's editable set); guard here rather than calling
        # it on nothing. An honest empty frontier, never a fabricated dispatch.
        comp.dispatch = {"path": "frontier", "reason": "empty or unparseable input (no tokens)"}
        comp.intent = "empty"
        return comp

    if kind == "question":
        rel = _cg.compose_relation(frame)
        comp.relation = rel
        semantic_evidence = _language_adapter_evidence(
            agent, frame, rel, kind="question")
        if semantic_evidence:
            comp.dispatch["language_evidence"] = semantic_evidence
        rule_name = _detect_reflexive_rule(substrate, gaps)
        has_cue = _has_self_cue(frame)
        if semantic_evidence.get("repair_evidence") == "unresolved_selection":
            # Selection residuals are repair evidence, not evidence that the
            # grammatical addressee makes this a self/meta question.
            comp.reflexive = False
            comp.dispatch = {
                "path": "frontier",
                "reason": "unresolved selection referent",
                "language_evidence": semantic_evidence,
            }
            comp.intent = "repair:unresolved_selection"
            return comp
        comp.reflexive = bool(rule_name) or has_cue
        if comp.reflexive:
            # Compute the strong keyword reading FIRST so a dedicated self_* faculty
            # (e.g. self_shape) can win over a SPURIOUS rule-name grounding: a gap
            # token that happens to be a common self-topic word ("shape") may exact-
            # match a held RuleSummary named/keyworded the same word, which would
            # otherwise preempt the self_shape faculty and repeat that program's
            # description instead of a fresh self-shape read. A GENUINE specific rule
            # name (e.g. "recover_shape_law", "chosen_action") is never one of a
            # self_* meta entry's own match fragments, so it keeps its priority.
            lex = _cq.load_meta_lexicon()
            words = _all_words(frame)
            entry, score = _best_meta_entry(lex, words, has_cue)
            kw_target = entry["meta_target"] if (entry and score > 0) else None
            if rule_name and kw_target and str(kw_target).startswith("self_"):
                frags = {_cq._norm(f) for f in (entry.get("match") or [])}
                if _cq._norm(rule_name) in frags:
                    rule_name = None                      # self_* faculty wins
            # OPERATIONAL SELF-INTROSPECTION — a reflexive 'how do you <verb>' /
            # 'how does <self-process> work' PROCESS question the agent HOLDS a
            # true self-account for (a taught SelfProcess: learning=collapse,
            # perceiving=sd-decode, world-attachment=adapter-ingest). A held
            # account is a strong grounded signal — it BEATS the generic keyword
            # overlap (which otherwise dumps the machinery inventory for
            # 'how do you perceive?') but stays below a specific held rule name,
            # and is only computed for a manner NON-structure question (a genuine
            # STRUCTURE question — 'how are you organised/composed?' — keeps its
            # self_organisation routing). Nothing is fabricated: find_self_process
            # returns None unless the agent genuinely holds the account, and then
            # the honest floor below still fires (byte-identical) for that gap.
            process_key = None
            if frame.get("focus") == "manner" and not _asks_self_structure(frame):
                try:
                    process_key = _self_model.find_self_process(substrate, words)
                except Exception:
                    process_key = None
            if rule_name:
                meta_target, meta_arg, strategy = "self_model_rule", rule_name, "rule_name_grounded"
            elif process_key:
                meta_target, meta_arg, strategy = "self_process", process_key, "self_process_grounded"
            elif kw_target:
                meta_target = kw_target
                meta_arg = _capture_meta_arg(entry, text)
                strategy = "keyword_overlap"
            elif rel.get("focus") == "polar" and _is_polar_capability_question(rel):
                verb = rel["predicate"]["surface"].strip(",.;:?!")
                assumption = _hypothetical_assumption(frame, text)
                if assumption:
                    comp.dispatch = {"path": "imagine_capability", "verb": verb,
                                      "assumption": assumption,
                                      "strategy": "hypothetical_polar"}
                    comp.intent = f"imagine_capability:{verb}:if_had_{assumption}"
                else:
                    comp.dispatch = {"path": "honest_capability", "verb": verb,
                                      "strategy": "polar_capability"}
                    comp.intent = f"ask_capability:{verb}"
                return comp
            elif frame.get("focus") == "manner" and not _asks_self_structure(frame):
                # A generic reflexive "how do you <verb>" / "how does X come about"
                # the agent has NO specific self-account for (no held-rule name, no
                # keyword-scored meta faculty, and NOT a self-STRUCTURE question). The
                # old wh_default mapped every "manner" -> self_organisation, dumping the
                # DOMAIN LIST as a non-sequitur ("how do you learn?" -> "I am organised
                # into ..."). Route instead to the HONEST self-process floor. A genuine
                # self-STRUCTURE question ("how are you put together / organised /
                # composed?") still falls through to self_organisation below (`_asks_
                # self_structure`), as do questions a keyword/table hit already scored.
                verb, self_process = _self_process_verb(frame)
                comp.dispatch = {"path": "honest_self", "verb": verb,
                                  "self_process": self_process,
                                  "strategy": "honest_self_process"}
                comp.intent = "honest_self:no_specific_account"
                return comp
            else:
                meta_target = _WH_DEFAULT_META.get(frame.get("focus"))
                meta_arg = None
                strategy = "wh_default"
            if meta_target:
                comp.dispatch = {"path": "meta", "meta_target": meta_target,
                                  "meta_arg": meta_arg, "strategy": strategy}
                comp.intent = f"ask_self:{meta_target}"
            else:
                comp.dispatch = {"path": "frontier",
                                  "reason": "reflexive question but no meta_target derivable "
                                            f"(focus={frame.get('focus')!r})"}
                comp.intent = "ask_self:unresolved"
        else:
            topic_el = _topic_nominal(rel)
            topic = topic_el["surface"].strip(",.;:?!") if topic_el else None
            pre_resolved = None
            if substrate is not None:
                try:
                    pre_resolved = _cg.resolve_focus(rel, [], substrate)
                except Exception:
                    pre_resolved = None
            if topic or pre_resolved:
                comp.dispatch = {"path": "know", "concept": topic, "pre_resolved": pre_resolved}
                if semantic_evidence:
                    # Preserve adapter-provided world/deixis evidence when the
                    # ordinary topic dispatch is materialized.  Without this
                    # carry-forward, a lexical Concept can erase a missing
                    # scene dependency before cognition arbitrates grounding.
                    comp.dispatch["language_evidence"] = semantic_evidence
                comp.intent = f"ask_world:{topic}"
            else:
                comp.dispatch = {"path": "frontier",
                                  "reason": "no topic nominal found in the composed relation"}
                comp.intent = "ask_world:unresolved"
    elif kind == "instruction":
        rel = _cg.compose_relation(frame)
        comp.relation = rel
        semantic_evidence = _language_adapter_evidence(
            agent, frame, rel, kind="instruction")
        rule_name = _detect_reflexive_rule(substrate, gaps)
        if rule_name:
            # an indirect information request ("Tell me about the rule X") —
            # a GROUNDED rule name promotes the imperative to a question,
            # mirroring the project's existing "tell"-is-a-question precedent.
            comp.kind = "question"
            comp.reflexive = True
            comp.dispatch = {"path": "meta", "meta_target": "self_model_rule",
                              "meta_arg": rule_name, "strategy": "rule_name_grounded_imperative"}
            comp.intent = f"ask_self:self_model_rule"
        else:
            # the PREDICATE is the frame's leading verb directly (`_classify_kind`
            # already established `first_is_verb` for this branch) — NOT
            # `rel["predicate"]`, which (for a matrix verb followed by an embedded
            # free-relative clause, "describe WHAT you see") picks the clause's
            # LAST verb (`compose_relation` is a single-clause composer, honestly
            # documented as such; a multi-clause imperative is a real residual,
            # reported below, not patched around).
            first = _first_element(frame)
            predicate = first["surface"].strip(",.;:?!") if first else None
            obj = rel.get("object") or rel.get("oblique")
            if semantic_evidence.get("action_predicate"):
                predicate = semantic_evidence["action_predicate"]
            if semantic_evidence.get("action_target"):
                obj = {"surface": semantic_evidence["action_target"]}
            comp.dispatch = {"path": "instruction", "relation": rel,
                              "predicate": predicate,
                              "object": obj["surface"].strip(",.;:?!") if obj else None}
            if semantic_evidence:
                comp.dispatch["language_evidence"] = semantic_evidence
            pred_s = comp.dispatch["predicate"] or "?"
            obj_s = comp.dispatch["object"] or ""
            comp.intent = f"do:{pred_s}" + (f"({obj_s})" if obj_s else "")
    else:
        rel = _cg.compose_relation(frame)
        comp.relation = rel
        semantic_evidence = _language_adapter_evidence(
            agent, frame, rel, kind="statement")
        if semantic_evidence.get("repair_evidence") == "knowledge_deficit":
            comp.dispatch = {"path": "frontier", "relation": rel,
                             "reason": "knowledge deficit requires repair",
                             "language_evidence": semantic_evidence}
            comp.intent = "repair:knowledge_deficit"
            return comp
        comp.dispatch = {"path": "statement", "relation": rel}
        if semantic_evidence:
            comp.dispatch["language_evidence"] = semantic_evidence
        comp.intent = "assert"

    return comp


__all__ = ["Comprehension", "comprehend_text", "kind_signals"]

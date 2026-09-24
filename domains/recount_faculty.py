"""recount_faculty — READING IS WRITING REVERSED, applied to a whole document.

The Jabberwock already BUILDS a "describe what you see" faculty (see
``scripts/arc_self_report.py``): ``comprehend_describe`` (hear a DIRECTIVE ->
mint a describe-Goal) + ``communicate_what_i_see`` (for each recognised
PERCEPT, mint a produce-utterance SUBGOAL sourced from the recognition) are
composed LIVE by the agent's own self-build machinery
(``reflective_faculty.induce_concern`` / ``ground_concern``). This module
builds the READ twin: "recount what you read" -- the same TWO rules, framed
from a recount-shaped concern instead of a perception-shaped one, reading
their utterance content from the SITUATION MODEL a document read built
(``comprehension_reader.read_and_comprehend``) instead of from a perceived
Scene's Percepts.

WHAT'S REUSED VERBATIM VS. WHAT'S A DISCOVERED, NAMED LIMIT (found by
inspection + live probing, not assumed):

  * ``communicate_what_i_see`` (composed via ``_compose_communicate_rule`` /
    its graph-resident twin ``compose_communicate_graph``) is genuinely
    GENERAL: its match/effects never hard-code an English word -- it fires on
    the STRUCTURAL shape ``goal -describes-> scene -has_percept-> percept
    -is_a-> concept``, whatever those nodes actually hold. So the READ twin
    needs no new composer call for the subgoal-minting step at all: it is the
    SAME rule, reused unmodified, once the read situation model is projected
    into that shape (`_project_read_scene`, below -- mechanical I/O, the
    same kind ``arc_self_report.py``'s ``main()`` uses to mint the visual
    Scene/Percept graph by hand).

  * The comprehension-directive composer (``_compose_comprehension_rule`` /
    its graph-resident twin), by contrast, is presently a PILOT: verified
    LIVE (feed it ``induce_concern(agent, [["hear","the","recount",
    "DIRECTIVE"], ...])`` and read the rule it installs) that its
    describe-fallback branch is HARD-CODED to the literal directive word
    ``'describe'`` and the literal Goal kind ``'describe_scene'`` / edge
    names ``'describes'``/``'described_by'``, regardless of the NL tokens
    handed to ``induce_concern`` -- the SAME rule
    (``comprehend_describe_directive_<tag>``, matching ``text == 'describe'``)
    comes out no matter what the concern's own words say. Generalising that
    builder to read its directive word from the concern itself means editing
    ``reflective_faculty.py``, which is explicitly OUT OF SCOPE for this
    build (protected file). So: the SAME literal ``'describe'`` directive
    word is what the composed rule actually needs to fire, and the
    demonstrated instruction is phrased "Describe what you read." (the exact
    read-twin of "Describe what you see."). So a human saying "recount"/
    "summarize" ALSO reaches the faculty, `world_receive_recount` mints ONE
    extra synonym-bridge Mention carrying the literal text the rule needs,
    ALONGSIDE (never REPLACING) the interlocutor's own words -- a thin,
    documented I/O-boundary normalisation of exactly the kind CLAUDE.md
    permits ("a thin I/O-boundary classifier is permitted ... when there's
    no Rust primitive that can do the job" -- true today; the real fix
    belongs in ``reflective_faculty.py``'s comprehension composer, named here
    as a residual, not silently worked around).

  * The production voice (`domains.language_production.LanguageProduction`)
    fills each grammatical ROLE with exactly ONE lexical item (one concept ->
    one surface word) -- verified live that a multi-word LexEntry surface
    ("justice department") never matches the self-monitor's own
    one-token-per-regex-word tokenizer, corrupting the round-trip. So a
    multi-word situation-model entity name ("justice_department",
    "big_oil_captured_government") is reduced to its HEAD word (last
    underscore part -- English compounds are head-final) before being handed
    to `produce()`. This is LOSSY (see the module-level report this build
    returns) but mechanical and uniform, not cherry-picked per example.

  * `_event_tense_probe` (``language_world.py``) recognises a concept as
    verb-shaped from SURFACE MORPHOLOGY alone (``-ed``, a small irregular
    past list, or trailing ``-s``) -- verified live that a bare, uninflected
    read verb ("join") produces a frame with NO recovered event at all (the
    self-monitor can't see it as a verb), while a present-tense-shaped noun
    ("fuels") gets MISTAKEN for one. The bridge therefore inflects a regular
    read verb to its past surface (`_past_surface`, a plain +ed/+d rule --
    mechanical morphology, the exact kind ``language_production.py``'s own
    docstring already documents as a known limitation of the reused
    lexicon-in-reverse) and reports "past" tense uniformly (a recount is
    retrospective by nature). A read predicate that is itself a closed-class
    preposition (an honest READING residual -- the situation-model reader
    mis-extracted the true verb, e.g. "promoted the burning OF fossil fuels"
    -> predicate "of") is not force-fit into a fake verb slot: it is skipped
    and reported as a residual, not silently mis-rendered.

None of this is a Python DECISION about what a sentence MEANS -- every
content word, every role assignment (subject/verb/object), and every
utterance the agent speaks came from the reading's own predications
(`comprehension_reader.read_and_comprehend`) and the composer's own rules.
This module's Python is world-adapter I/O: run the reader, mechanically
re-expose its surfaces (the lexicon bridge), mechanically project its
predications into the SAME graph shape the describe faculty's composed rule
already reads, and mechanically read the resulting utterance frames back out
to hand to `LanguageProduction.produce` -- exactly ``self_report``'s role in
``arc_self_report.py``, one hop further (through the ``about`` edge to the
percept's bound Concept instead of reading attrs off the subgoal directly,
since the composer's OWN rule -- read verbatim above -- is what wires content
onto ``con``, not onto ``sg``).
"""
from __future__ import annotations

from typing import Any, Optional

from domains import actor_goals as ag
from domains import comprehension_reader as cr
from domains.conversation_action import smooth_scene_prose
from domains.reflective_faculty import induce_concern, ground_concern

try:
    from domains import audience_driven_production as adp
except Exception:                                    # pragma: no cover
    adp = None


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _captured_passive_agent(sub, verb: str, patient: str) -> Optional[str]:
    """The by-phrase agent media_analysis captured for this passive
    (`PassivePredication{verb,patient,agent,agent_filled}`) -- a mechanical graph
    read, no decision (the agent identity is media_analysis's by-phrase capture,
    made when it read the clause). Returns the captured agent slug iff an
    agent-FILLED passive matches this (verb, patient), else None."""
    for pp in sub.nodes("PassivePredication"):
        at = sub.node(pp)["attrs"]
        if (str(at.get("verb")) == str(verb)
                and str(at.get("patient")) == str(patient)
                and float(at.get("agent_filled") or 0.0) == 1.0):
            got = str(at.get("agent") or "")
            if got:
                return got
    return None


# --------------------------------------------------------------------------- #
#  THE FACULTY -- the agent BUILDS comprehend_recount + communicate_what_i_
#  read via its own self-build composer. I only frame the concerns (the NL
#  token lists below); the rule bodies printed by "[self-build] minted live
#  rule ..." are the composer's own authorship, not hand-written here.
# --------------------------------------------------------------------------- #

_COMPREHEND_TAG = "comprehend_recount"
_COMMUNICATE_TAG = "communicate_what_i_read"
# deterministic rule names the composer's builders always produce for the
# above tags (see module docstring) -- used ONLY as an idempotency probe
# (mechanical name lookup, the SAME discipline reflective_faculty.py's own
# `existing_names` guards use), never to author or alter a rule body.
_COMPREHEND_RULE_NAME = "comprehend_describe_directive_" + _COMPREHEND_TAG
_COMMUNICATE_RULE_NAME = "communicate_what_i_see_" + _COMMUNICATE_TAG


def faculty_built(agent) -> bool:
    """Mechanical name lookup -- has this agent already had the recount
    faculty composed? (Idempotency probe only; never a content decision.)"""
    sub, native = _resolve(agent)
    names = {r.get("name") for r in native.export_rules() if isinstance(r, dict)}
    return _COMPREHEND_RULE_NAME in names and _COMMUNICATE_RULE_NAME in names


def build_recount_faculty(agent) -> dict[str, Any]:
    """The agent BUILDS its own 'recount what I read' comprehend + communicate
    rules via the self-build composer (``induce_concern``/``ground_concern``)
    -- the SAME two-call shape ``arc_self_report.build_describe_faculty`` uses
    for ``comprehend_describe``/``communicate_what_i_see``. Idempotent (a
    second call on an agent that already has the faculty is a no-op)."""
    if faculty_built(agent):
        return {"already_built": True}
    cA = induce_concern(agent, [["hear", "the", "recount", "DIRECTIVE"],
                                ["mint", "a", "GOAL"]],
                        name_hint=_COMPREHEND_TAG)
    ground_a = ground_concern(agent, [cA["capability_key"]]) if cA.get("capability_key") else None
    cB = induce_concern(agent, [["told", "RECOUNT", "what", "READ"],
                                ["for_each", "READ_EVENT", "mint", "SUBGOAL"],
                                ["SUBGOAL", "produces", "UTTERANCE"],
                                ["source", "UTTERANCE", "from", "READ_EVENT"]],
                        name_hint=_COMMUNICATE_TAG)
    ground_b = ground_concern(agent, [cB["capability_key"]]) if cB.get("capability_key") else None
    return {"already_built": False, "comprehend": cA, "comprehend_ground": ground_a,
            "communicate": cB, "communicate_ground": ground_b}


# --------------------------------------------------------------------------- #
#  THE LEXICON BRIDGE -- the surface of every read word is already known (it
#  was just read); re-expose it as a LexEntry so the production voice can say
#  it. Mechanical: no meaning decided, only re-exposing what the reading
#  already saw. See the module docstring for the two morphology bridges this
#  needs (multi-word -> head word; bare verb -> past-inflected surface) and
#  why -- both are DISCOVERED requirements of the REUSED production/parse
#  pipeline, verified live, not invented complexity.
# --------------------------------------------------------------------------- #

_IRREGULAR_PAST = frozenset({
    "sat", "broke", "chased", "ate", "ran", "wrote", "gave", "came",
    "bought", "cut", "made", "went", "took", "told", "said", "saw",
})


def _cased_lookup(text: str) -> dict[str, str]:
    """lower word -> first-seen ORIGINAL casing, off the source text. Pure
    mechanical index over the surfaces the reading already saw."""
    out: dict[str, str] = {}
    for w in text.split():
        clean = w.strip(",.;:!?()\"'")
        if clean and clean.lower() not in out:
            out[clean.lower()] = clean
    return out


def entity_phrase(text: str, slug: str, cased: Optional[dict[str, str]] = None) -> str:
    """Re-expose a situation-model entity slug ('justice_department') as the
    FULL cased surface phrase the reading already saw ('Justice Department'),
    by looking each underscore-part up in the ORIGINAL text. PURE MECHANICAL
    STRING I/O: it re-assembles what was read; it makes NO realization
    decision -- no head-picking, no collapse. WHICH parts become the noun vs a
    modifier, and WHETHER the whole entity is realized at all, are the
    ``seeds/recount_realization.json`` rules' decisions, not this helper's.
    (This is the exact analogue of perception mechanically separating a
    Percept's ``shape`` and ``colour`` for ``describe_utterance``'s rules to
    route -- see that seed.)"""
    cased = cased if cased is not None else _cased_lookup(text)
    parts = [p for p in slug.split("_") if p]
    return " ".join(cased.get(p, p) for p in parts) if parts else slug


def _np_word_count_from_production(words: list, role: str) -> int:
    """Mechanical READ-OFF of how many whitespace-separated WORDS
    `prod.produce`'s OWN phonological_word sequence used to realize a given
    frame ROLE's noun phrase (the content word + any immediately preceding
    function word -- e.g. a determiner: 'the'+'oil company' = 3 words for
    role='agent' when 'the' is grounded and the multi-word entity phrase is
    'oil company', itself ONE phonological_word entry whose surface contains
    a space -- see bridge_lexicon_entry's multi-word-as-one-lexical-item
    note). This is not a re-derivation or a guess: it counts what production
    ACTUALLY emitted (words[i]['role'] == role for the content word, plus the
    run of immediately preceding 'fn:*'-tagged tokens that belong to the SAME
    noun phrase -- determiners precede their noun in en/es, see language_
    production._function_words_for_slot), each entry's OWN surface split on
    whitespace (never assumed to be one word). Used only to know how many
    LEADING/TRAILING words of an ALREADY-PRODUCED clause a fluency elision
    may mechanically strip -- never to decide WHETHER to elide (that is
    recount_fluency.json's rule)."""
    def _word_count(entry: dict) -> int:
        surface = str(entry.get("surface") or "")
        return len(surface.split()) if surface else 1
    idx = next((i for i, w in enumerate(words) if w.get("role") == role), None)
    if idx is None:
        return 0
    count = _word_count(words[idx])
    j = idx - 1
    while j >= 0 and str(words[j].get("role") or "").startswith("fn:"):
        count += _word_count(words[j])
        j -= 1
    return count


def _past_surface(verb_lower: str) -> str:
    """Regular +ed inflection (mechanical morphology -- the SAME kind of
    surface-only bridge ``_lemmatize``/``_event_tense_probe`` already are in
    ``language_world.py``), so a bare read verb becomes verb-shaped to the
    SAME morphology probe the self-monitor's re-parse uses. Irregulars /
    already-inflected surfaces pass through unchanged."""
    if verb_lower in _IRREGULAR_PAST or verb_lower.endswith("ed"):
        return verb_lower
    if verb_lower.endswith("e"):
        return verb_lower + "d"
    return verb_lower + "ed"


def bridge_lexicon_entry(world, surface: str, concept: Optional[str] = None) -> None:
    """Re-expose ONE read surface to the production voice, via the world's
    OWN lexicon-grounding primitive (``_add_lex_entry`` -- the SAME mechanism
    comprehension training uses, not a bespoke one). By default concept ==
    surface (identity): the concept string carries the case/properness signal
    production reads (``concept[:1].isupper()``). A MULTI-WORD entity passes an
    explicit ``concept`` (its cased phrase) distinct from the lower-cased
    stored surface, so the space-containing surface resolves as ONE lexical
    item through the latin multi-word tokenizer (``LanguageWorld._parse_with_
    grounded``) and the self-monitor round-trip recovers the whole entity. The
    STORED LexEntry surface is lower-cased (mirroring ``LanguageWorld._ground``'s
    own normalisation) so the tokenizer -- which lower-cases -- finds it again."""
    world._add_lex_entry("en", surface.lower(), concept or surface,
                         source="reading_bridge")


# --------------------------------------------------------------------------- #
#  SALIENCE ORDER -- read off discourse_coherence's own centrality Argmax
#  (mechanical re-read, no new decision: the DECISION was Argmax's / the
#  display-sort precedent `centrality_ranking` itself documents).
# --------------------------------------------------------------------------- #

def _salience_order(agent, comp_result: dict) -> list[int]:
    """Sentence indices (into ``spine.textbase``) in SALIENCE order -- the
    centrality-ranked order ``discourse_coherence`` already computed (most
    central first; ties preserve text order, guaranteed by
    ``argmax_matches_top_of_sort``). Falls back to plain text order when no
    ranking exists."""
    sub, native = _resolve(agent)
    textbase = comp_result["spine"]["textbase"]
    ranking = (comp_result.get("centrality") or {}).get("ranking") or []
    if not ranking:
        return list(range(len(textbase)))
    order: list[int] = []
    for row in ranking:
        node = row.get("node")
        if node is None:
            continue
        try:
            sent_order = sub.node(node)["attrs"].get("order")
        except Exception:
            continue
        if isinstance(sent_order, (int, float)):
            order.append(int(sent_order))
    seen: set = set()
    out = [i for i in order if not (i in seen or seen.add(i))]
    for i in range(len(textbase)):
        if i not in seen:
            out.append(i)
    return out


# --------------------------------------------------------------------------- #
#  PROJECT THE READ SITUATION MODEL -- PURE MECHANICAL INGEST (no decisions).
#  For each read predication [rel, a0, a1] it writes the RAW structure onto a
#  Percept/Concept in the SAME scene -has_percept-> percept -is_a-> concept
#  shape the composed `communicate_what_i_read` rule reads: the agent/patient
#  entity's FULL cased surface phrase (`recount_agent`/`recount_patient` --
#  NO head-collapse, NO skip), the past-inflected predicate surface
#  (`recount_pred`), the raw predicate lemma (`recount_pred_lemma`, the skip
#  guard's input) and the raw slugs. It DECIDES NOTHING: whether a predication
#  is a realizable event (vs a mis-extracted preposition), and how each entity
#  fills the produce-frame slots (say_agent/say_event/say_patient), are the
#  `seeds/recount_realization.json` RULES' decisions -- run below, then read
#  back. (The head-picking `head_surface` and the skip `is_function_predicate`
#  that used to live here are DELETED; their decisions are now those rules.)
# --------------------------------------------------------------------------- #

def project_read_scene(agent, world, article_text: str, comp_result: dict) -> dict:
    """Ingest the read predications as raw graph data, run the realization
    rules, and read their decisions back. Returns
    {"scene": NodeID, "n_events": int, "residuals": [...]} -- ``residuals`` is
    read off the ``recount_residual`` marks the ``recount_residual_mark`` RULE
    set (a mis-extracted preposition predicate), never a Python skip."""
    sub, native = _resolve(agent)
    # Reconcile-wire the fluency codebooks (seeds/recount_fluency.json's
    # ConnectiveMap / PronounMap) to the agent hub -- the SAME mechanical
    # reconcile-by-presence idiom actor_goals.py's own goal-layer codebooks
    # use (ensure_opposing_pair_codebook etc.), reused verbatim so a
    # teach()-taught row reaches the fluency rules' join without a fresh
    # boot. Mechanical seed I/O, not a decision.
    ag._wire_codebook_by_key(agent, "ConnectiveMap", "has_connective_map", "relation")
    ag._wire_codebook_by_key(agent, "PronounMap", "has_pronoun_map", "role")
    textbase = comp_result["spine"]["textbase"]
    # COREF-RESOLVED args: the recount reads the RESOLVED comprehension state,
    # not the raw pre-coref textbase -- the coref layer's own decisions (a
    # multi-token proper name kept whole "robert" -> "robert_levy" [phase 3];
    # a pronoun bound to its referent "he" -> "levy") are graph state, and
    # using them is mechanical I/O, not a recount decision. `spine["ingests"]`
    # is the flat, textbase-ORDER list of resolved predications; slice it per
    # sentence (the same cum-indexing `reading_drive._mint_sentence_parse_nodes`
    # uses) so a salience-ordered read still picks the right resolved args.
    ingests = comp_result["spine"].get("ingests") or []
    resolved_by_sent: dict = {}
    _cum = 0
    for _si, _tb in enumerate(textbase):
        _n = len(_tb.get("predications") or [])
        resolved_by_sent[_si] = [list(r.get("predication") or [])
                                 for r in ingests[_cum:_cum + _n]]
        _cum += _n
    cased = _cased_lookup(article_text)
    scene = sub.add_node("Scene", {})
    order_i = 0
    cons: list[tuple] = []                    # (con_node, sentence, [rel,a0,a1])
    for sent_idx in _salience_order(agent, comp_result):
        tb = textbase[sent_idx]
        raw_preds = tb.get("predications") or []
        res_preds = resolved_by_sent.get(sent_idx) or []
        for pi, rec in enumerate(raw_preds):
            if len(rec) < 3:
                continue
            # Prefer the coref-resolved predication (same shape, resolved args);
            # fall back to the raw one if coref produced no parallel record.
            res = res_preds[pi] if pi < len(res_preds) and len(res_preds[pi]) >= 3 else rec
            rel, a0, a1 = str(res[0]), str(res[1]), str(res[2])
            if a0 in ("_", ""):
                # PASSIVE with a DELETED agent ("was funded" -> subject slot is
                # the '_' placeholder). media_analysis already CAPTURED the
                # by-phrase agent on a PassivePredication{verb,patient,agent,
                # agent_filled} node -- graph state, its decision. Read it back
                # (mechanical) so the recount says "the oil company funded ..."
                # instead of "the _ funded ...". Absent a captured agent (a
                # genuinely agentless passive), leave the placeholder.
                cap = _captured_passive_agent(sub, rel, a1)
                if cap:
                    a0 = cap
            agent_phrase = entity_phrase(article_text, a0, cased)
            patient_phrase = entity_phrase(article_text, a1, cased)
            pred_surface = _past_surface(rel.lower())
            # Re-expose every surface to the production voice (mechanical). A
            # multi-word entity is grounded as ONE lexical item (surface with a
            # space, cased concept), so it round-trips whole through the latin
            # multi-word tokenizer; the predicate surface grounds as itself.
            bridge_lexicon_entry(world, agent_phrase, concept=agent_phrase)
            bridge_lexicon_entry(world, patient_phrase, concept=patient_phrase)
            bridge_lexicon_entry(world, pred_surface)
            con = sub.add_node("Concept", {
                "recount_agent": agent_phrase, "recount_patient": patient_phrase,
                "recount_pred": pred_surface, "recount_pred_lemma": rel.lower(),
                "recount_agent_slug": a0, "recount_patient_slug": a1,
                "order": order_i, "sentence": tb.get("sentence")})
            p = sub.add_node("Percept", {"order": order_i})
            native.add_edge_unchecked(scene, "has_percept", p)
            native.add_edge_unchecked(p, "is_a", con)
            cons.append((con, tb.get("sentence"), [rel, a0, a1]))
            order_i += 1
    native_steps = native.run_rules()        # the realization + fluency rules DECIDE here
    receipt = sub.add_node("NativeRecountReceipt", {
        "schema": "native_recount_receipt.v1",
        "cluster": "recount_faculty.read_scene_settlement",
        "provenance": "native_rule_readback:recount_realization",
        "native_rule": "recount_realization_and_fluency_rules",
        "event_count": len(cons),
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    # Re-expose the fixed fluency vocabulary (event words + connective/pronoun
    # surfaces) held as seed data (seeds/recount_fluency.json's
    # `RecountVocabulary` rows) -- mechanical bridging of DATA the seed
    # declares, the SAME pattern project_analysis_scene already uses for its
    # own AnalysisVocabulary, never a Python-hardcoded English word list.
    for vnd in sub.nodes("RecountVocabulary"):
        surface = sub.node(vnd)["attrs"].get("surface")
        if surface:
            bridge_lexicon_entry(world, surface)
    # Read back the rules' residual decision (mechanical query, no Python skip).
    residuals: list[dict] = []
    for con, sentence, pred in cons:
        if not native.has_node(con):
            continue
        if sub.node(con)["attrs"].get("recount_residual") == 1.0:
            residuals.append({
                "sentence": sentence, "predication": pred,
                "reason": ("recount_event_realizable declined this predication: its "
                           "predicate lemma '%s' is a closed-class preposition in the "
                           "held codebook, not an event verb -- the situation-model "
                           "reader mis-extracted the true verb; the rule marked it a "
                           "residual, not faked" % pred[0])})
    return {"scene": scene, "n_events": order_i, "residuals": residuals}


# --------------------------------------------------------------------------- #
#  THE WORLD RECEIVER -- mechanical ingest of the DIRECTIVE (mirrors
#  ``arc_self_report.world_receive`` exactly), plus the documented synonym
#  bridge (see module docstring: the composer's comprehension builder only
#  recognises the literal word 'describe').
# --------------------------------------------------------------------------- #

_RECOUNT_SYNONYMS = frozenset({"recount", "summarize", "summarise", "recap"})


def world_receive_recount(agent, scene, instruction: str) -> None:
    """THE WORLD'S LANGUAGE RECEIVER for a recount directive -- translate an
    external instruction into a Message the agent perceives (about the read
    scene). Mechanical ingest; no utterance authored here. Every one of the
    interlocutor's own words is minted as its own Mention, UNCHANGED; if none
    of them is the literal word the composed rule matches ('describe') but
    one IS a recognised recount/summarize synonym, ONE extra Mention carrying
    'describe' is minted ALONGSIDE them (tagged, never replacing) -- see the
    module docstring for why this is needed and why it's an honest, named
    residual rather than a silent synonym substitution."""
    sub, native = _resolve(agent)
    msg = sub.add_node("Message", {"text": instruction})
    native.add_edge_unchecked(msg, "about", scene)
    words = instruction.lower().replace(".", "").replace("?", "").split()
    for w in words:
        native.add_edge_unchecked(msg, "has_mention", sub.add_node("Mention", {"text": w}))
    if "describe" not in words and any(w in _RECOUNT_SYNONYMS for w in words):
        bridge = sub.add_node("Mention", {"text": "describe", "synonym_bridge": True,
                                          "synonym_of": next(w for w in words if w in _RECOUNT_SYNONYMS)})
        native.add_edge_unchecked(msg, "has_mention", bridge)


# --------------------------------------------------------------------------- #
#  THE READ-OFF -- mechanically assembles each subgoal's utterance FRAME from
#  graph state (the composer's own rule wired content onto ``con`` via the
#  ``about`` edge -- see module docstring) and calls the REAL production
#  voice. No template: every string in ``lines`` is `prod.produce`'s own
#  ``overt_speech``.
# --------------------------------------------------------------------------- #

def recount_report(agent, prod, *, parent_kind: str = "describe_scene",
                   scene=None, audience: Optional[dict] = None) -> dict:
    """EMIT the recount. For each produce-utterance subgoal minted off a
    ``parent_kind`` Goal (optionally scoped to one ``scene``), read the frame
    the composer's rule bound via ``sg -about-> con`` and speak it through
    ``prod.produce``. When ``audience`` is given (an
    ``audience_driven_production.audience_model`` result), a subgoal whose
    WHOLE concept set the audience already knows (``residual_vs_audience``,
    reused verbatim) is not uttered -- real audience design: don't restate
    what this listener already has. donkey=0 always (no LLM call anywhere in
    this path).

    ALSO reads back three FLUENCY decisions seeds/recount_fluency.json's
    rules may have written onto ``con`` (recount_connective /
    recount_elide_agent / recount_pronoun_patient -- absent on every
    analysis-layer reading node, so this is a no-op there): ``connectives``/
    ``elide_leading``/``elide_trailing`` are returned as lists PARALLEL to
    ``lines``, for ``smooth_scene_prose`` to apply as mechanical glue over the
    ALREADY-PRODUCED clause text (the DECISIONS -- which relation gets which
    connective, which subject/object is a repeat -- are the rules'; the word
    COUNT to strip is read straight off what `prod.produce` itself emitted,
    via `_np_word_count_from_production`, never re-guessed)."""
    sub, native = _resolve(agent)
    goals = [g for g in sub.nodes("Goal") if native.has_node(g)
             and sub.node(g)["attrs"].get("kind") == parent_kind
             and (scene is None or scene in native.neighbours(g, "describes"))]
    subgoals = [sg for g in goals for sg in native.neighbours(g, "has_subgoal")]
    rows: list[tuple] = []
    skipped_known: list[dict] = []
    for sg in subgoals:
        if not native.has_node(sg):
            continue
        cons = list(native.neighbours(sg, "about"))
        if not cons:
            continue
        con = cons[0]
        cat = sub.node(con)["attrs"]
        agent_w = cat.get("say_agent")
        if not agent_w:
            continue
        event_w, patient_w = cat.get("say_event"), cat.get("say_patient")
        meaning = {x for x in (agent_w, event_w, patient_w) if x}
        uttered = True
        if audience is not None and adp is not None:
            residual = adp.residual_vs_audience(agent, meaning, audience)
            uttered = residual["residual_frac"] > 0.0
        if not uttered:
            skipped_known.append(cat)
            continue
        goal = {"agent": agent_w, "tense": "past", "intent": "inform"}
        if event_w:
            goal["event"] = event_w
        if patient_w:
            goal["patient"] = patient_w
        production = prod.produce("en", goal)
        words = production["phonological_word"]["words"]
        elide_lead = 0
        if cat.get("recount_elide_agent") == 1.0:
            elide_lead = _np_word_count_from_production(words, "agent")
        elide_trail = None
        pronoun = cat.get("recount_pronoun_patient")
        if pronoun:
            n_drop = _np_word_count_from_production(words, "patient")
            if n_drop:
                elide_trail = (n_drop, pronoun)
        rows.append((cat.get("order", 0), production, True,
                    cat.get("recount_connective"), elide_lead, elide_trail))
    rows.sort(key=lambda r: r[0])
    return {
        "n_goals": len(goals), "n_subgoals": len(subgoals),
        "lines": [r[1]["overt_speech"] for r in rows],
        "productions": [r[1] for r in rows],
        "accepted": [r[1]["accepted"] for r in rows],
        "connectives": [r[3] for r in rows],
        "elide_leading": [r[4] for r in rows],
        "elide_trailing": [r[5] for r in rows],
        "skipped_known_to_audience": skipped_known,
    }


# --------------------------------------------------------------------------- #
#  THE CLEAN ENTRY POINT -- read the article, build the faculty if needed,
#  project the situation model, receive the directive, read off the recount.
#  Register-shaped via `smooth_scene_prose` (reused, not reimplemented).
# --------------------------------------------------------------------------- #

def recount_what_read(agent, world, prod, article_text: str, *,
                      instruction: str = "Recount what you read.",
                      register: str = "neutral",
                      audience: Optional[dict] = None) -> dict:
    """The recount faculty, end to end. `world`/`prod` are an ALREADY-TRAINED
    ``LanguageWorld``/``LanguageProduction`` pair (the SAME construction
    ``arc_self_report.main`` uses) -- production reads the grounded grammar
    back out, so the world must exist before this bridges the read lexicon
    into it. Returns {"prose": str, "lines": [...], "residuals": [...],
    "n_goals": int, "n_subgoals": int, "accepted": [...], "productions": [...]}."""
    build_recount_faculty(agent)
    comp = cr.read_and_comprehend(agent, article_text)
    projection = project_read_scene(agent, world, article_text, comp)
    world_receive_recount(agent, projection["scene"], instruction)
    sub, native = _resolve(agent)
    native_steps = native.run_rules()       # the instruction enters reasoning (comprehend -> communicate)
    sub.add_node("NativeRecountReceipt", {
        "schema": "native_recount_receipt.v1",
        "cluster": "recount_faculty.recount_reasoning_settlement",
        "provenance": "native_rule_readback:recount_reasoning",
        "native_rule": "recount_faculty_reasoning_rules",
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    report = recount_report(agent, prod, scene=projection["scene"], audience=audience)
    # FLUENCY: the smoother reads the agent's OWN held connective/elision
    # decisions (seeds/recount_fluency.json's rules, read back by
    # recount_report above) -- it decides nothing itself. Absent on a plain
    # article with no fired relation/repeat (every entry None/0), this is
    # byte-identical to the plain Oxford-"and" join smooth_scene_prose always
    # did (see its own docstring for the equivalence).
    prose = smooth_scene_prose(report["lines"], register=register,
                               connectives=report.get("connectives"),
                               elide_leading=report.get("elide_leading"),
                               elide_trailing=report.get("elide_trailing"))
    return {
        "prose": prose, "lines": report["lines"], "productions": report["productions"],
        "accepted": report["accepted"], "n_goals": report["n_goals"],
        "n_subgoals": report["n_subgoals"], "residuals": projection["residuals"],
        "skipped_known_to_audience": report["skipped_known_to_audience"],
        "comprehension": comp,
    }


# --------------------------------------------------------------------------- #
#  THE ANALYSIS LAYER -- READING IS WRITING REVERSED, one level up: the agent
#  writes ANALYTICAL prose about what it INFERRED, not just what happened.
#
#  The goal-layer / epistemic READINGS this realizes (ConflictingGoalsReading,
#  SurfaceInversionReading, TemporalConflictReading, TropeReading,
#  EpistemicLeanReading) are ALREADY GRAPH STATE by the time this runs -- they
#  were minted by `actor_goals.py`'s own agent-authored classify-by-join rules
#  while `cr.read_and_comprehend` ran (see `reading_drive._shim_meaning_
#  inference`, which auto-fires the conflicting-goals / surface-inversion /
#  temporal-conflict / named-trope / epistemic-evidence layers per sentence).
#  This module NEVER mints a reading -- `project_analysis_scene` is a PURE
#  READER + MECHANICAL PROJECTOR, exactly the role `project_read_scene` plays
#  for the surface events one section up.
#
#  THE ONE thing that decides which reading FIELD becomes which produce-frame
#  slot (agent / event / patient) lives ENTIRELY in
#  `seeds/recount_analysis_realization.json` -- five small rules, one per
#  reading TYPE, each keyed by a decorated-attr discriminator that is unique
#  to that type (see that seed's own docstring). Python here is type-BLIND:
#  it decorates EVERY short string attr on EVERY held reading node the SAME
#  way, regardless of which reading type it belongs to, and lets the rules
#  pick. Ablating one rule drops exactly that reading type's sentence --
#  proof the frame-construction decision is the rule's, never a Python
#  if/elif over reading type (see
#  ``test_recount_analysis_migrated.py::test_frame_construction_is_a_rule_not_python``).
#
#  REUSE, not new composition: the realized reading nodes are wired into the
#  SAME `scene -has_percept-> p -is_a-> con` shape `project_read_scene`
#  already uses, so the ALREADY-COMPOSED `communicate_what_i_see_
#  communicate_what_i_read` rule (self-built once, by `build_recount_
#  faculty`, structurally generic over what `con` holds -- see the module
#  docstring) fires unmodified for the analysis scene too. No second
#  induce_concern/ground_concern call is needed; the same one general rule
#  serves both scenes, exactly as the module docstring's "the READ twin needs
#  no new composer call" claim already established for the surface layer.
# --------------------------------------------------------------------------- #

_ANALYSIS_READING_TYPES = ("ConflictingGoalsReading", "SurfaceInversionReading",
                          "TemporalConflictReading", "TropeReading",
                          "EpistemicLeanReading")
_ANALYSIS_PHRASE_MAX_WORDS = 6   # mechanical length bound (mirrors
                                # `_utterance_ngrams`'s own MAX_N convention) --
                                # excludes long free-text fields (a TropeReading's
                                # `gloss`) from decoration/bridging, not a
                                # per-field content decision.


def _phrase(text: str) -> str:
    """Mechanical surface-decoration for a SYNTHESIZED (not read-off-the-
    article) slug / composite key a goal-layer codebook holds: '_'/'-' become
    a space, '|' (a composite pair_key's ordering marker, 'fund|oppose')
    becomes ' then ' so the two joined verbs stay readable as a sequence.
    Pure `str` work, no `import re`, no meaning decision -- the SAME status as
    `entity_phrase`'s underscore split above, generalised to the punctuation
    the goal-layer codebooks (tension / reading / pair_key) actually use."""
    out = str(text).replace("|", " then ").replace("_", " ").replace("-", " ")
    return " ".join(out.split())


def _named_phrase(text: str) -> str:
    """Title-cased `_phrase` -- marks a synthesized phrase as a NAMED unit so
    `LanguageProduction`'s EXISTING properness signal (`concept[:1].isupper()`,
    already how 'Trojan Horse' / 'Justice Department' skip the determiner)
    treats it the same way, for free. Pure mechanical casing; no content
    decision -- the value's WORDS are unchanged, only their case."""
    return _phrase(text).title()


def _decorate_reading_phrases(sub, nd) -> None:
    """GENERIC, type-BLIND mechanical decoration: for every SHORT
    (<= `_ANALYSIS_PHRASE_MAX_WORDS` words) string attr a held reading node
    carries, write a `<key>_phrase` sibling holding its `_named_phrase`
    surface. Applies UNIFORMLY regardless of the reading's TYPE or which
    fields it happens to hold -- there is no per-type branch here. WHICH
    decorated field a produce-frame slot reads is entirely
    `seeds/recount_analysis_realization.json`'s own static Attr key, never
    decided here."""
    at = dict(sub.node(nd)["attrs"])
    for k, v in at.items():
        if not isinstance(v, str) or not v or k.endswith("_phrase"):
            continue
        if len(_phrase(v).split()) > _ANALYSIS_PHRASE_MAX_WORDS:
            continue                    # too long to be a name/phrase (e.g. a gloss sentence)
        sub.set_attr(nd, k + "_phrase", _named_phrase(v))


def project_analysis_scene(agent, world, article_text: str) -> dict:
    """Ingest the agent's OWN held goal-layer / epistemic readings -- ALREADY
    graph state, never minted here -- as a produce-ready Scene, mechanically:
    for each held reading node of `_ANALYSIS_READING_TYPES` not yet projected,
    decorate its short string attrs (`_decorate_reading_phrases`), bridge
    every decorated phrase to the production lexicon (`bridge_lexicon_entry`,
    reused verbatim), and wire a fresh Percept -is_a-> THE READING NODE
    ITSELF into a new Scene (no separate Concept copy is minted -- the
    reading node already IS the concept the composed communicate rule reads
    `say_*` off of). Then runs `seeds/recount_analysis_realization.json`'s
    rules, whose per-type Eq/Not-Exists joins DECIDE which decorated field
    fills `say_agent`/`say_event`/`say_patient` -- see the section docstring.
    Idempotent (`analysis_projected` guard): a reading already projected by an
    earlier call is not re-projected (would otherwise double-utter it via a
    fresh Percept). Returns {"scene": NodeID, "n_readings": int} -- 0 readings
    on a plain article with no fired goal-layer analysis is HONEST: nothing is
    fabricated when nothing was inferred.

    ALSO reconcile-wires the FLUENT PHRASING codebooks
    (seeds/recount_analysis_realization.json's `TensionPhrasing`/
    `PairPhrasing`, v1.1.0) to the agent hub -- the SAME mechanical
    reconcile-by-presence idiom `project_read_scene` already uses for
    ConnectiveMap/PronounMap, reused verbatim -- so a teach()-taught phrasing
    row reaches `analysis_say_conflicting_goals_fluent`/`analysis_say_
    temporal_conflict_fluent`'s join without a fresh boot. Mechanical seed
    I/O, not a decision: WHICH tension/pair gets a fluent phrase (vs. the
    mechanical slug fallback) is entirely those rules' own Eq/Not-Exists
    join against this codebook."""
    sub, native = _resolve(agent)
    ag._wire_codebook_by_key(agent, "TensionPhrasing", "has_tension_phrasing", "tension")
    ag._wire_codebook_by_key(agent, "PairPhrasing", "has_pair_phrasing", "pair_key")
    scene = sub.add_node("Scene", {})
    order_i = 0
    for rtype in _ANALYSIS_READING_TYPES:
        for nd in sub.nodes(rtype):
            if sub.node(nd)["attrs"].get("analysis_projected") == 1.0:
                continue
            _decorate_reading_phrases(sub, nd)
            at = sub.node(nd)["attrs"]
            for k, v in at.items():
                if isinstance(v, str) and k.endswith("_phrase") and v:
                    bridge_lexicon_entry(world, v, concept=v)
            sub.set_attr(nd, "order", order_i)
            sub.set_attr(nd, "analysis_projected", 1.0)
            p = sub.add_node("Percept", {"order": order_i})
            native.add_edge_unchecked(scene, "has_percept", p)
            native.add_edge_unchecked(p, "is_a", nd)
            order_i += 1
    # Re-expose the fixed analysis vocabulary (event words + the generic
    # 'reading' subject) held as seed data (seeds/recount_analysis_
    # realization.json's `AnalysisVocabulary` rows) -- mechanical bridging of
    # DATA the seed declares, never a Python-hardcoded English word list.
    for vnd in sub.nodes("AnalysisVocabulary"):
        surface = sub.node(vnd)["attrs"].get("surface")
        if surface:
            bridge_lexicon_entry(world, surface, concept=surface)
    # Re-expose every held FLUENT PHRASING codebook row (TensionPhrasing /
    # PairPhrasing) as a multi-word LexEntry, the SAME mechanism the
    # decorated `_phrase` bridging loop above uses -- these values are
    # already-cased DATA (like TropeSignature.trope), never re-titled here.
    for cb_type in ("TensionPhrasing", "PairPhrasing"):
        for vnd in sub.nodes(cb_type):
            phrase = sub.node(vnd)["attrs"].get("phrase")
            if phrase:
                bridge_lexicon_entry(world, phrase, concept=phrase)
    native_steps = native.run_rules()      # rules DECIDE say_* here
    sub.add_node("NativeRecountReceipt", {
        "schema": "native_recount_receipt.v1",
        "cluster": "recount_faculty.analysis_scene_settlement",
        "provenance": "native_rule_readback:recount_analysis_scene",
        "native_rule": "recount_analysis_realization_rules",
        "reading_count": int(order_i),
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    return {"scene": scene, "n_readings": order_i}


def analyse_what_read(agent, world, prod, article_text: str, *,
                      instruction: str = "Recount what you read.",
                      register: str = "neutral",
                      audience: Optional[dict] = None,
                      actor_classes: Optional[dict[str, str]] = None) -> dict:
    """The recount faculty PLUS the analysis layer, end to end. Reuses
    `recount_what_read` UNCHANGED for the surface events, then realizes
    whatever goal-layer / epistemic readings the read already produced (plus,
    when `actor_classes` supplies a {actor: class} WORLD FACT, calls the
    agent's OWN `actor_goals.annotate_actor_class` + `assess_epistemic_lean`
    -- both already-documented mechanical orchestration, see their own
    docstrings -- so the epistemic verdict reflects the supplied context).
    `actor_classes` is a caller-supplied external fact (exactly like
    `annotate_actor_class`'s own contract) -- never inferred here from the
    text; omit it and the epistemic layer simply reflects whatever the reads'
    OWN structural signal-detectors already produced.

    Returns everything `recount_what_read` returns PLUS `surface_prose`/
    `analysis_prose`/`surface_lines`/`analysis_lines`, and a combined `prose`
    that is the surface recount's OWN produced sentence followed by the
    analysis scene's OWN produced sentence (events, then the reading of
    them) -- both independently generated by `prod.produce`, only their two
    ALREADY-COMPLETE strings are concatenated here."""
    surface = recount_what_read(agent, world, prod, article_text,
                                instruction=instruction, register=register,
                                audience=audience)
    if actor_classes:
        for actor, actor_class in actor_classes.items():
            ag.annotate_actor_class(agent, actor, actor_class)
        ag.assess_epistemic_lean(agent)
    projection = project_analysis_scene(agent, world, article_text)
    sub, native = _resolve(agent)
    analysis_report = {"lines": [], "productions": [], "accepted": [],
                       "n_goals": 0, "n_subgoals": 0, "skipped_known_to_audience": []}
    if projection["n_readings"]:
        world_receive_recount(agent, projection["scene"], instruction)
        native_steps = native.run_rules()
        sub.add_node("NativeRecountReceipt", {
            "schema": "native_recount_receipt.v1",
            "cluster": "recount_faculty.analysis_reasoning_settlement",
            "provenance": "native_rule_readback:recount_analysis_reasoning",
            "native_rule": "recount_analysis_reasoning_rules",
            "reading_count": int(projection["n_readings"]),
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        analysis_report = recount_report(agent, prod, scene=projection["scene"], audience=audience)
    analysis_prose = smooth_scene_prose(analysis_report["lines"], register=register)
    combined_prose = surface["prose"]
    if analysis_prose:
        combined_prose = (combined_prose + " " + analysis_prose).strip()
    return {
        "prose": combined_prose,
        "surface_prose": surface["prose"], "analysis_prose": analysis_prose,
        "surface_lines": surface["lines"], "analysis_lines": analysis_report["lines"],
        "lines": surface["lines"] + analysis_report["lines"],
        "productions": surface["productions"] + analysis_report["productions"],
        "accepted": surface["accepted"] + analysis_report["accepted"],
        "n_goals": surface["n_goals"] + analysis_report["n_goals"],
        "n_subgoals": surface["n_subgoals"] + analysis_report["n_subgoals"],
        "n_readings": projection["n_readings"],
        "residuals": surface["residuals"],
        "skipped_known_to_audience": (surface["skipped_known_to_audience"]
                                      + analysis_report["skipped_known_to_audience"]),
        "comprehension": surface["comprehension"],
    }


__all__ = ["build_recount_faculty", "faculty_built", "project_read_scene",
          "world_receive_recount", "recount_report", "recount_what_read",
          "entity_phrase", "bridge_lexicon_entry",
          "project_analysis_scene", "analyse_what_read"]

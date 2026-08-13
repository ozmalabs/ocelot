"""inference_generation — STEP 3: GENERATE THE UNSTATED INFERENCE.

situation_model_reader (step 2) builds a situation model but only GROUNDS/
INFERS from what the text STATES: bare "John dropped the glass." reaches
`on_floor` (the `fell` premise the event supplied) but never `broken`,
because `event_reasoning.json`'s `infer_broken` rule also needs `fragile` on
the theme, and nothing in the bare sentence states it. That is an honest
RESIDUAL, not a bug — fragility is WORLD KNOWLEDGE, not textbase content.

This module closes the residual with ONE mechanism, used for TWO kinds of
gap (Haviland & Clark's given-new bridging is the same shape as an enabling-
condition inference — both are "an inter-proposition gap collapsed against a
knowledge codebook", not two different procedures):

  1. GAP-DETECT (mechanical graph read, no decision):
     · a WORLD-KNOWLEDGE gap is a stalled `event_reasoning.json` rule
       precondition: an `is_entity` SmEntity that satisfies every conjunct
       of some rule's `where` EXCEPT ONE (`detect_precondition_gaps`) — read
       GENERICALLY off the rule JSON (never a hardcoded "if attr==fragile"
       branch: the rule file names its own conjuncts, this only checks which
       one the resident entity is missing);
     · a BRIDGING gap is a definite-NP subject of a property predication
       ("the beer was warm") that carries no `part_of` link yet
       (`detect_bridging_gaps`) — the Haviland & Clark given-new signal, no
       lexical cue (no "which is part of..." marker needed).

  2. DECODE (the collapse — `reflective_faculty.compose_design_for_goal`,
     the SAME Rust `ShapeDecode` Term `reading_collapse.py` uses for
     construction recognition, reused as-is): the gap is turned into a goal
     relation-system (`[["needs", entity, attr]]` or `[["needs_whole",
     entity]]`) and decoded against the `seeds/inference_knowledge.json`
     codebook (`ShapeSignature{kind:"knowledge_*"}` nodes). The WINNING
     schema is read off the decode's own ranking
     (`reading_collapse._winner`, reused, not re-implemented) — Python never
     picks which schema fires; a gap the codebook does not cover decodes to
     no winner and mints nothing (the honest, discriminative null).

  3. MINT (mechanical adapter I/O): the winning schema's own `supplies` attr
     (data: `{"relation": "is_a", "attr": ...}` or `{"relation": "part_of",
     "object": ...}`) — read off the WINNING node, never guessed — names
     the fact to write. An enabling-condition fact is minted via
     `situation_model_reader.ingest_predication` (UNCHANGED, reused as-is:
     its own property-predication branch sets the attr AND re-runs
     `run_rules`, so the stalled chain completes). A bridging fact is a
     direct `part_of` edge (mechanical `add_edge`, mirroring
     `reading_collapse._write_predications`'s own admissibility-gated
     write), since `part_of` is not a change-of-state verb `ingest_
     predication` would otherwise mint.

  4. GATE — `standard_of_coherence` (a single `StandardOfCoherence` node,
     `depth` in {"shallow","deep"}): a schema tagged `coherence:"blocking"`
     (an enabling condition or a bridging link — BOTH classical accounts
     agree these are drawn, because without them the text is either
     contradictory or the definite reference is infelicitous) always fires.
     A schema tagged `coherence:"elaborative"` (glass -> made_of_glass: true
     but not needed by anything) fires ONLY when the node's `depth` reads
     "deep" — McKoon & Ratcliff's minimalist reader stops at the blocking
     set; Graesser's constructionist reader keeps going. The gate is a plain
     attribute comparison (like `reading_collapse`'s own `write`/`learn`
     mode flags) — it decides WHETHER a pass runs, never WHICH schema wins.

ARCHITECTURE (CLAUDE.md). The decision that carries content — WHICH schema
covers a gap — is the ShapeDecode collapse's, read off its own `plan`/
`shape_fit`/`residual` (via the held `reading_collapse._winner`, not
reimplemented); the state MUTATION is the existing `run_rules` fixpoint
(situation_model_reader.ingest_predication, unchanged) plus one mechanical
`add_edge` for the bridging case. Gap DETECTION reads graph state (which
rule conjuncts are satisfied, which entity carries no `part_of` edge) but
never decides the CONTENT of an inference. No `if`/`else` selects the
inferred relation; no `import re`; donkey = 0 (no LLM, arithmetic + the held
matcher).
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import discourse_coherence as dc
from domains import instruction_reading as ir
from domains import reading_collapse as rc
from domains import reflective_faculty as rf
from domains import situation_model_reader as smr
from domains.reference_resolution import _PRONOUNS

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED = os.path.join(_ROOT, "seeds", "inference_knowledge.json")
_EVENT_REASONING_SEED = os.path.join(_ROOT, "seeds", "event_reasoning.json")
_LOGICAL_SEED = os.path.join(_ROOT, "seeds", "inference_logical.json")


# --------------------------------------------------------------------------- #
#  resolution + seed install (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def ensure_seeds(agent) -> None:
    """Idempotently install seeds/inference_knowledge.json (the knowledge
    codebook + the StandardOfCoherence gate node), plus its dependency
    (situation_model / event_reasoning, via smr.ensure_seeds — reused). Guard
    is the sentinel Concept 'inference_knowledge', the SAME idiom every other
    domains/*.py ensure_seeds uses. Mechanical seed I/O."""
    smr.ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    if _has_concept(sub, "inference_knowledge"):
        _ensure_warning_lexicon(agent)   # additive; safe on an already-loaded graph
        _ensure_trust_lexicon(agent)     # additive; safe on an already-loaded graph
        return
    with open(_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))


def ensure_logical_seeds(agent) -> None:
    """Idempotently install seeds/inference_logical.json (the
    'knowledge_logical' codebook -- held propositional implications, DEDUCTION_
    GENERALIZATION_PREREG.md/_RESULTS.md), depending on ensure_seeds
    (inference_knowledge + event_reasoning). Guard is the sentinel Concept
    'inference_logical', the SAME idiom ensure_seeds uses for
    'inference_knowledge'. ADDITIVE ONLY: seeds/inference_knowledge.json itself
    is never read or written here -- this installs a SEPARATE seed file into
    the SAME ShapeSignature codebook pool (a new `kind`, not a new node type;
    see SHAPE_TYPE_VOCABULARY_SPIKE.md's corrected finding that node TYPE, not
    `kind`, partitions a decode pool)."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    if _has_concept(sub, "inference_logical"):
        return
    with open(_LOGICAL_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))


def _ensure_warning_lexicon(agent) -> None:
    """Install the WarningLexicon node if absent (a graph that loaded an OLDER
    inference_knowledge.json, e.g. a persona boot, would not carry it). Additive
    graph I/O — the licensing gate needs the codebook resident; `detect_warning_
    gaps` still falls back to the same defaults if it is somehow missing, so this
    is belt-and-braces, never a decision."""
    sub, _, _ = _resolve(agent)
    for _ in sub.nodes("WarningLexicon"):
        return
    sub.add_node("WarningLexicon", {"forms": ["beware", "shun"],
                                    "anchor": ["beware", "shun", "avoid"],
                                    "threshold": 0.5, "licensed_response": "slay"})


def _ensure_trust_lexicon(agent) -> None:
    """Install the TrustLexicon node if absent (a graph that loaded an OLDER
    inference_knowledge.json would not carry it). The STANCE-RELATIVE trust
    codebook the embedded-reading licensing gate reads. Additive graph I/O —
    `trust_membership` falls back to the same defaults if it is somehow missing,
    so this is belt-and-braces, never a decision."""
    sub, _, _ = _resolve(agent)
    for _ in sub.nodes("TrustLexicon"):
        return
    sub.add_node("TrustLexicon", {
        "trusted_anchor": ["son", "child", "daughter", "father", "mother", "kin"],
        "untrusted_anchor": ["stranger", "enemy", "foe", "adversary"],
        "threshold": 0.5})


# --------------------------------------------------------------------------- #
#  STANDARD OF COHERENCE — the single tunable depth gate.
# --------------------------------------------------------------------------- #
def _coherence_node(sub):
    for n in sub.nodes("StandardOfCoherence"):
        return n
    return None


def coherence_depth(agent) -> str:
    """Read the current standard_of_coherence depth ("shallow"/"deep")."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    node = _coherence_node(sub)
    return (sub.node(node)["attrs"].get("depth") if node is not None else "shallow") or "shallow"


def set_coherence_depth(agent, depth: str) -> None:
    """Set the standard_of_coherence depth — a plain graph-data tunable
    (like reading_collapse's write/learn flags), not an agent decision. The
    caller picks "shallow" (minimalist, McKoon & Ratcliff) or "deep"
    (constructionist, Graesser)."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    node = _coherence_node(sub)
    if node is not None:
        sub.set_attr(node, "depth", str(depth))


def _is_deep(agent) -> bool:
    return coherence_depth(agent) == "deep"


# --------------------------------------------------------------------------- #
#  WORLD-KNOWLEDGE / ENABLING-CONDITION GAP — a stalled rule precondition,
#  read GENERICALLY off seeds/event_reasoning.json (never a hardcoded attr).
# --------------------------------------------------------------------------- #
_RULE_CACHE: Optional[list] = None


def _rule_conditions(rule: dict) -> list:
    """[(key, literal_value), ...] — the Eq(Attr(x,key),Lit(v)) conjuncts of
    a rule's `where` (a bare Eq, or an And{items:[...]} of them). The SAME
    "items = where.get('items',[where])" idiom situation_model_reader.
    _verb_frames already uses to read this seed family. Mechanical seed
    read — no attribute name is hardcoded here."""
    where = rule.get("where", {})
    items = where.get("items", [where]) if isinstance(where, dict) else []
    conds = []
    for it in items:
        if not isinstance(it, dict) or it.get("type") != "Eq":
            continue
        a = it.get("a", {})
        if a.get("type") == "Attr" and a.get("node", {}).get("name") == "x":
            conds.append((a.get("key"), it.get("b", {}).get("value")))
    return conds


def _rule_effect_attr(rule: dict) -> Optional[str]:
    for eff in rule.get("effects", []):
        if isinstance(eff, list) and len(eff) >= 3 and eff[0] == "set_attr":
            return eff[2]
    return None


def _stateful_rules() -> list:
    """The event_reasoning rules matched on `[x, is_entity, x]` with at
    least one Eq(Attr) precondition and a set_attr effect — cached (the
    seed file is static). Read once, generic across every such rule (three
    today: infer_on_floor / infer_broken / infer_worthless), so a future
    rule added to that seed is picked up with NO change here."""
    global _RULE_CACHE
    if _RULE_CACHE is not None:
        return _RULE_CACHE
    try:
        with open(_EVENT_REASONING_SEED) as f:
            seed = json.load(f)
    except Exception:
        seed = {"rules": []}
    out = []
    for r in seed.get("rules", []):
        if r.get("match") != [["x", "is_entity", "x"]]:
            continue
        conds = _rule_conditions(r)
        eff = _rule_effect_attr(r)
        if conds and eff:
            out.append({"name": r.get("name"), "conds": conds, "effect": eff})
    _RULE_CACHE = out
    return out


def detect_precondition_gaps(agent, unit=None) -> list:
    """Every resident SmEntity that is EXACTLY ONE conjunct away from firing
    some MULTI-CONJUNCT event_reasoning rule (all-but-one of the rule's Eq
    preconditions already hold — genuine PARTIAL progress — the rule's own
    effect attr not yet set) — a rule precondition the text left unfilled,
    blocking local coherence. Returns [{entity, node, rule, need_attr,
    need_value}].

    A rule with only ONE conjunct (infer_on_floor needs just `fell`;
    infer_worthless needs just `broken`) is NEVER reported here: an unset
    single precondition on an entity that never triggered the event at all
    is not "one fact away from coherence", it is simply inapplicable — a
    stalled gap requires at least one conjunct ALREADY true (partial
    evidence) with exactly one still missing. A rule with >1 missing
    conjunct is likewise out of scope (not "one fact away")."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    gaps = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        name = at.get("name")
        if not name:
            continue
        if unit is not None and at.get("unit") != unit:   # FLOW-SCOPED (Wave 1A)
            continue
        for rule in _stateful_rules():
            if len(rule["conds"]) < 2 or at.get(rule["effect"]) == 1:
                continue                            # single-conjunct or already fired
            missing = [(k, v) for k, v in rule["conds"] if at.get(k) != v]
            if len(missing) == 1:
                gaps.append({"entity": name, "node": n, "rule": rule["name"],
                             "need_attr": missing[0][0], "need_value": missing[0][1]})
    return gaps


# --------------------------------------------------------------------------- #
#  BRIDGING GAP — a definite NP with no discourse antecedent (no part_of).
# --------------------------------------------------------------------------- #
def detect_bridging_gaps(agent, textbase: list, unit=None) -> list:
    """Every FIRST-mentioned property-predication subject ("the beer was
    warm" -> is_a(beer, warm)) whose surface was introduced with a definite
    determiner ("the") and which carries no `part_of` link yet — the
    Haviland & Clark given-new bridging signal: a definite NP with NO
    resident antecedent. `textbase` is situation_model_reader's own
    per-sentence predication list (reused, not re-parsed). Thin I/O-boundary
    check only (substring test for "the <surface>" in the lowercased
    sentence — CLAUDE.md's permitted carve-out: converting an opaque
    surface cue into the smallest graph token, no regex). Returns
    [{entity, sentence}]."""
    sub, _, _ = _resolve(agent)
    seen: set = set()
    gaps = []
    for tb in textbase:
        sentence = str(tb.get("sentence", ""))
        low = sentence.lower()
        for p in tb.get("predications", []):
            if len(p) < 3:
                continue
            rel, a0 = str(p[0]), str(p[1])
            if not smr._is_property_pred(rel):
                continue
            if a0 in seen or a0.lower() in _PRONOUNS:
                seen.add(a0)
                continue
            seen.add(a0)
            surface = a0.replace("_", " ")
            definite = ("the " + surface) in low
            ent = None
            for m in sub.nodes("SmEntity"):
                mat = sub.node(m)["attrs"]
                if mat.get("name") == a0 and (unit is None or mat.get("unit") == unit):
                    ent = m
                    break
            has_whole = bool(ent is not None and sub.neighbours(ent, "part_of"))
            if definite and not has_whole:
                gaps.append({"entity": a0, "sentence": sentence})
    return gaps


# --------------------------------------------------------------------------- #
#  GOAL-FROM-STATE GAP — a character SmEntity carrying a NEED-STATE (thirsty/
#  hungry/afraid/...) but no goal yet: the fable never says the crow 'wanted'
#  water, desire is implicit in 'thirsty' -- the SAME gap shape as bridging
#  (a fact the text left implicit, felicity-required to make the character's
#  later action explicable), decoded against a need->remedy codebook instead
#  of a part-whole one.
# --------------------------------------------------------------------------- #
_NON_CANDIDATE_PREFIXES = ("coref_",)
_NON_CANDIDATE_KEYS = ("goal", "name")


def detect_goal_gaps(agent, unit=None) -> list:
    """Every resident, NON-NESTED SmEntity carrying a NEED-STATE attr (any
    attr==1, excluding coref bookkeeping and the goal slot itself) but NO
    `goal` yet. One candidate per qualifying attr — mirrors `detect_
    elaborative_candidates`'s breadth (every resident fact is offered, the
    DECODE narrows to the genuine ones): this scan never hardcodes which attr
    NAME counts as a need-state (no `if attr == "thirsty"`); the codebook
    (`need_remedy_*` ShapeSignature schemas) is what actually recognises one,
    and an uncovered attr (`on_floor`, `broken`, `fell`, ...) decodes to no
    winner — an honest null, exactly like an uncovered `elaborate`/`needs`
    candidate elsewhere in this module. Returns [{entity, node, need_attr}]."""
    sub, _, _ = _resolve(agent)
    gaps = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        name = at.get("name")
        if unit is not None and at.get("unit") != unit:   # UNIT-SCOPED (MOVE 2b)
            continue
        if not name or at.get("nested") or at.get("goal") is not None:
            continue
        for k, v in at.items():
            if v != 1 or k in _NON_CANDIDATE_KEYS or k.startswith(_NON_CANDIDATE_PREFIXES):
                continue
            gaps.append({"entity": name, "node": n, "need_attr": k})
    return gaps


def _mint_goal(agent, entity_name: str, remedy: str, need_attr: Optional[str] = None,
               *, unit=None) -> dict:
    """Mechanical mint: the character's GOAL into the SAME slot character_
    tom's desire branch fills (`goal` attr on the character's own SmEntity,
    plus an SmEvent{verb:'want'} carrying the Zwaan & Radvansky
    `idx_intentionality` index — the identical graph shape `character_tom.
    _ground_attitude_complement`'s desire branch writes, so `character_tom.
    character_goal` reads it back with NO change to that module). character_
    tom exposes no standalone 'set the goal' writer (only the whole
    propositional-attitude-SENTENCE pipeline, which requires an explicit
    attitude verb) — so this mint mirrors `_mint_part_of`'s idiom: a direct,
    mechanical write of the SAME shape, not a call into character_tom's
    private machinery."""
    sub, native, _ = _resolve(agent)
    ent = smr._entity(agent, entity_name, unit=unit)
    if sub.node(ent)["attrs"].get("goal") == remedy:
        return {"entity": entity_name, "goal": remedy, "already": True}
    ev_attrs = {"verb": "want", "surface": "implicit_need", "active": 0}
    if unit is not None:
        ev_attrs["unit"] = unit
    event = sub.add_node("SmEvent", ev_attrs)
    _edge = smr._edge
    _edge(native, event, "agent", ent)
    sub.set_attr(event, "idx_protagonist", entity_name)
    sub.set_attr(event, "idx_intentionality", remedy)
    # ADDITIVE DURABLE MARKER (blackboard dissolution): persist the TRIGGERING
    # need-state ('thirsty'/'hungry') onto the want-SmEvent too -- literary_
    # analysis._build_summary reads it back ("The story follows a crow, which
    # is thirsty"). task 82 flagged this slot stored only the remedy; a stage
    # reads the need-attr, so it is now graph-resident.
    if need_attr is not None:
        sub.set_attr(event, "need_attr", need_attr)
    sub.set_attr(ent, "goal", remedy)
    return {"entity": entity_name, "goal": remedy, "event": smr._v(event)}


def _goal_is_licensed(agent, gap: dict) -> bool:
    """THE LICENSING GATE, goal level. A need-state candidate LICENSES a goal
    only when it is a WARRANTED motivation — a state the protagonist is
    genuinely IN, established by a declarative predication about them ('the crow
    was thirsty' -> is_a(crow, thirsty) -> crow.thirsty=1). A candidate carrying
    the `imperative_derived`/`unwarranted` provenance marker is NOT warranted:
    it was installed by an inherited warning/imperative directed AT the
    protagonist ('Beware the Jabberwock, my son!'), which asserts no state on
    them — the son is in no need-state, the danger is never established, so
    collapsing it into a heroic-quest goal would be an UNLICENSED collapse. Read
    off the candidate's own graph provenance, never a story literal: a declarative
    need-state (every mint today) is licensed; an imperative-derived one is held
    open. Byte-identical for the crow/afraid-son (declarative states carry no
    such marker)."""
    sub, _, _ = _resolve(agent)
    node = gap.get("node")
    if node is not None:
        at = sub.node(node)["attrs"]
        if at.get("imperative_derived") or at.get("unwarranted"):
            return False
    return True


def resolve_goal_gap(agent, gap: dict, *, unit=None) -> dict:
    """Resolve ONE goal-from-state gap: FIRST check the licensing gate
    (`_goal_is_licensed`) — an unwarranted (imperative-derived) need-state is
    HELD OPEN, never collapsed into a goal. A LICENSED need-state decodes
    `[["needs_goal", gap["need_attr"]]]` against the codebook — keyed on the
    NEED-STATE alone (not the entity's name), so the SAME `need_remedy_thirst`
    schema covers 'crow', 'wolf', or any other thirsty character — the winning
    `knowledge_goal` schema's `supplies` (`{"relation": "goal", "remedy":
    ...}`) is minted into the character_tom goal slot via `_mint_goal`. No
    covering schema -> honest null, nothing fabricated (a bare 'on_floor' or
    'broken' attr never resembles a need-state to the codebook)."""
    if not _goal_is_licensed(agent, gap):
        return {"minted": False, "held_open": True, "gap": gap, "schema": None,
                "reason": ("need-state %r is UNLICENSED (imperative-derived, no governing "
                           "felt need) -- the goal/motivation is deliberately UNDETERMINED, "
                           "held open, nothing fabricated") % (gap.get("need_attr"),)}
    dec = decode_gap(agent, [["needs_goal", gap["need_attr"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": gap, "schema": None,
                "reason": ("no need-remedy schema covers need-state %r -- honest null, "
                           "nothing fabricated") % (gap["need_attr"],)}
    sub, _, _ = _resolve(agent)
    coherence = _coherence_of(sub, dec["name"])
    if coherence == "elaborative" and not _is_deep(agent):
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    if supplies.get("relation") == "goal" and supplies.get("remedy"):
        eff = _mint_goal(agent, gap["entity"], supplies["remedy"], gap.get("need_attr"), unit=unit)
        return {"minted": True, "gap": gap, "schema": dec["name"], "supplies": supplies,
                "effect": eff}
    return {"minted": False, "gap": gap, "schema": dec["name"],
            "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}


# --------------------------------------------------------------------------- #
#  WARNING / IMPERATIVE GAP — the LICENSING DISTINCTION, one level up at
#  MEANING. An imperative caution clause ('Beware the Jabberwock, my son!') is a
#  DIRECTIVE to an addressee, not a state predication about a protagonist: it
#  names a THREAT but installs NO need-state, so a naive reader who collapses it
#  into a heroic-quest goal is performing an UNLICENSED collapse. When such a
#  warning is present AND no governing felt need is established anywhere in the
#  text, the goal is HELD OPEN: an OpenGoal + Ambiguity node RECORDS the
#  withholding (the graph holds the deliberate under-determination, not a
#  fabricated goal). This is collapse-only-when-licensed at the goal level.
# --------------------------------------------------------------------------- #
def _warning_lexicon(agent) -> tuple:
    """(forms:set, anchors:list, threshold:float) read off the resident
    WarningLexicon node (seeds/inference_knowledge.json), with the SAME defaults
    baked in if the node is somehow absent — graph-native codebook, never a
    hardcoded story rule. Mechanical seed read."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("WarningLexicon"):
        at = sub.node(n)["attrs"]
        forms = {str(f).lower() for f in (at.get("forms") or [])}
        anchors = [str(a).lower() for a in (at.get("anchor") or [])]
        try:
            thr = float(at.get("threshold", 0.5))
        except (TypeError, ValueError):
            thr = 0.5
        return forms, anchors, thr
    return {"beware", "shun"}, ["beware", "shun", "avoid"], 0.5


def warning_membership(agent, verb: str) -> dict:
    """Is `verb` a caution/avoid-danger IMPERATIVE verb? A SEED form resolves
    directly (via='member'); an unseen caution verb JOINS by adjacency — the
    SAME WordNet path-similarity signal (`rc._wordnet_nearness`) COS/ATTITUDE
    use — to the WarningLexicon anchors >= threshold. Below threshold -> not a
    warning verb (the discriminative null). Returns {lemma, warning, nearness,
    nearest, via}. Never a hardcoded verb list — the anchors are seed data."""
    forms, anchors, thr = _warning_lexicon(agent)
    lemma = smr._lemma(verb)
    if lemma in forms:
        return {"lemma": lemma, "warning": True, "nearness": 1.0,
                "nearest": lemma, "via": "member"}
    score, member = rc._wordnet_nearness(lemma, anchors)
    if member is not None and score >= thr:
        return {"lemma": lemma, "warning": True, "nearness": float(score),
                "nearest": member, "via": "adjacency"}
    return {"lemma": lemma, "warning": False, "nearness": float(score),
            "nearest": member, "via": None}


def detect_warning_gaps(agent, textbase: list) -> list:
    """Every sentence that OPENS with a WARNING-class imperative verb — a
    verb-INITIAL caution clause ('Beware the Jabberwock', 'Shun the frumious
    Bandersnatch'). The imperative signal is structural, not lexical: the FIRST
    recognised content word is a main-verb-headed WARNING member (`ir.
    is_verb_headed` + `warning_membership`), which marks a DIRECTIVE with no
    declarative subject-experiencer before it — so the clause asserts no state on
    anyone. Reuses `comprehend_text._recognise_words` (the SAME word recogniser
    character_tom's scan uses) — no regex. The THREAT is the first content word
    after the verb (function words stripped via rc's held marker lexicon); the
    ADDRESSEE, when a vocative possessive ('my son'/'thy child') is present, is
    the noun it governs — best-effort, recorded, never required. Returns
    [{sentence, verb, threat, addressee}]."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    lex = rc._marker_lexicon(sub)
    gaps = []
    for tb in textbase:
        sentence = str(tb.get("sentence", ""))
        words = ct._recognise_words(agent, sentence)
        if not words:
            continue
        head = str(words[0])
        if lex.get(head.lower()) is not None or not ir.is_verb_headed(head):
            continue                                  # not verb-initial -> not imperative
        mem = warning_membership(agent, head)
        if not mem["warning"]:
            continue
        # THREAT: first content word after the verb (skip function/DET words).
        threat = None
        addressee = None
        rest = [str(w) for w in words[1:]]
        for i, w in enumerate(rest):
            cls = lex.get(w.lower())
            if cls in ("POSS", "PRON") or w.lower() in ("my", "thy", "your", "his", "her"):
                # a vocative possessive -> the noun it governs is the addressee.
                if i + 1 < len(rest):
                    addressee = rest[i + 1].lower()
                continue
            if cls is not None:                       # DET / other function word
                continue
            if threat is None:
                threat = w.lower()
        gaps.append({"sentence": sentence, "verb": mem["lemma"],
                     "threat": threat, "addressee": addressee, "membership": mem})
    return gaps


def _any_licensed_need_state(agent, *, unit=None) -> bool:
    """Is any WARRANTED, felt need established anywhere in the resident model —
    a need-state a `need_remedy_*` schema actually covers? (This is exactly what
    `detect_goal_gaps` + the decode would license.) A warning grounded in such a
    need is not an unlicensed collapse; a warning with NONE (Jabberwocky: the son
    is in no need-state) is. Reuses the SAME detect + decode path — no new
    decision.

    Robust to the read ORDER: this runs AFTER the goal pass, so a need-state
    already LICENSED-and-minted now carries a `goal` attr (and detect_goal_gaps,
    which skips goal-bearing entities, no longer offers it). A resident goal
    minted from a felt need therefore ALSO counts — so a text with BOTH a
    warning and a genuine felt need ('The son was afraid. Beware the
    Jabberwock!') licenses, it does not hold open."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if not at.get("nested") and at.get("goal") is not None:
            return True                               # a felt need already licensed a goal
    for g in detect_goal_gaps(agent, unit=unit):
        dec = decode_gap(agent, [["needs_goal", g["need_attr"]]])
        if dec["name"] is not None and dec["fit"] > 0:
            return True
    return False


def resolve_warning_gap(agent, gap: dict, *, unit=None) -> dict:
    """THE LICENSING GATE for a warning. A warning LICENSES a goal only if the
    text ALSO establishes a governing felt need (`_any_licensed_need_state`) —
    then the ordinary goal-from-state path already infers it and this records
    nothing new. With NO governing need-state (the son of Jabberwocky: an
    inherited 'Beware X' and no established danger to him), the goal is
    UNLICENSED: HOLD OPEN. Mint an `OpenGoal` + an `Ambiguity` node RECORDING
    'the goal/motivation is deliberately UNDETERMINED' — the graph holds the
    withholding itself, never a fabricated goal. Returns {held_open, licensed,
    open_goal, ambiguity, gap}."""
    if _any_licensed_need_state(agent, unit=unit):
        return {"held_open": False, "licensed": True, "gap": gap,
                "reason": ("a governing felt need is established -- the warning is grounded; "
                           "the ordinary goal-from-state path infers it, nothing withheld")}
    sub, native, _ = _resolve(agent)
    record = "the goal/motivation is deliberately UNDETERMINED"
    og_attrs = {"protagonist": gap.get("addressee") or "unspecified",
                "threat": gap.get("threat") or "unspecified",
                "warning_verb": gap.get("verb"), "held_open": 1, "licensed": 0,
                "record": record, "about": "goal",
                "reason": ("an inherited warning/imperative applies but the protagonist "
                           "carries no governing need-state -- the danger is never "
                           "established, so the motivation is not warranted by the text"),
                "source": "inference_generation"}
    open_goal = sub.add_node("OpenGoal", dict(og_attrs))
    amb_attrs = {"about": "goal", "threat": gap.get("threat") or "unspecified",
                 "record": record, "held_open": 1, "warning_verb": gap.get("verb"),
                 "source": "inference_generation"}
    ambiguity = sub.add_node("Ambiguity", dict(amb_attrs))
    smr._edge(native, open_goal, "has_ambiguity", ambiguity)
    return {"held_open": True, "licensed": False, "gap": gap,
            "open_goal": smr._v(open_goal), "ambiguity": smr._v(ambiguity),
            "record": record}


# --------------------------------------------------------------------------- #
#  STANCE-RELATIVE LICENSING — a warning is licensed WITHIN a belief-world iff
#  that world TRUSTS the source. THE SAME warning that is UNLICENSED as
#  OBJECTIVE FACT (the detached reader can't verify -> held open, above) is
#  LICENSED as the CHILD's BELIEF: the child trusts the father (a kin vocative
#  fixes the source-addressee relation), so within the child's nested belief-
#  world the warning licenses 'the named threat is dangerous' and the quest to
#  slay it. Licensing is RELATIVE TO THE BELIEF-WORLD / STANCE — two verdicts,
#  one warning, decided by WHOSE world frames the read.
#
#  DECOUPLING (the maturity, per the reader-response correction): the licensed
#  danger-belief lives ONLY in the child's NESTED belief-world (character_tom's
#  belief_world idiom), indexed to the child by `belief_holder`. It is a MODELED
#  object — it NEVER leaks into the reader's own belief set. The reader's own
#  verdict stays the detached hold-open (resolve_warning_gap, unchanged). This
#  module mints the modeled child-belief; reader_response records that the
#  reader models it WITHOUT holding it (boundary maintained, not collapsed).
# --------------------------------------------------------------------------- #
def _trust_lexicon(agent) -> tuple:
    """(trusted:set, untrusted:set, threshold:float) read off the resident
    TrustLexicon node (seeds/inference_knowledge.json), with the SAME defaults
    baked in if the node is somehow absent — graph-native codebook, never a
    hardcoded story rule. Mechanical seed read."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("TrustLexicon"):
        at = sub.node(n)["attrs"]
        trusted = {str(f).lower() for f in (at.get("trusted_anchor") or [])}
        untrusted = {str(f).lower() for f in (at.get("untrusted_anchor") or [])}
        try:
            thr = float(at.get("threshold", 0.5))
        except (TypeError, ValueError):
            thr = 0.5
        return trusted, untrusted, thr
    return ({"son", "child", "daughter", "father", "mother", "kin"},
            {"stranger", "enemy", "foe", "adversary"}, 0.5)


def trust_membership(agent, vocative: str) -> dict:
    """Does the addressee TRUST the warning's source? The addressee-vocative
    ('my SON') fixes the source-addressee relation: a KIN vocative names family
    (a TRUSTED source WITHIN the addressee's belief-world); an ADVERSARIAL
    vocative (stranger/enemy/foe) names an UNTRUSTED source. Resolved by SEED
    MEMBERSHIP against the TrustLexicon anchors (graph data) — NOT WordNet
    generalization: the held nearness signal `rc._wordnet_nearness` is VERB-only
    (pos='v') and trust vocatives are NOUNS, so a lexicon of members is the
    honest, graph-native mechanism (a vocative outside the lists is `unknown` ->
    conservatively NOT trusted, the discriminative null). Returns {vocative,
    trusted, polarity, via}. Never a hardcoded 'father'/'jabberwock' literal."""
    ensure_seeds(agent)
    trusted, untrusted, _thr = _trust_lexicon(agent)
    low = str(vocative or "").lower()
    if low in trusted:
        return {"vocative": low, "trusted": True, "polarity": "trusted", "via": "member"}
    if low in untrusted:
        return {"vocative": low, "trusted": False, "polarity": "untrusted", "via": "member"}
    return {"vocative": low, "trusted": False, "polarity": "unknown", "via": None}


def _licensed_response(agent) -> str:
    """The QUEST a BELIEVED danger-warning licenses within a believer's world
    ('slay') — read off the WarningLexicon's `licensed_response` seed attr, never
    a Python literal for the story's response."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("WarningLexicon"):
        r = sub.node(n)["attrs"].get("licensed_response")
        if r:
            return str(r)
    return "slay"


def resolve_warning_embedded(agent, gap: dict) -> dict:
    """THE STANCE-RELATIVE licensing gate. The SAME warning `resolve_warning_gap`
    held open as OBJECTIVE FACT is LICENSED WITHIN the addressee's belief-world
    IFF that world TRUSTS the source (`trust_membership` on the addressee
    vocative — a kin vocative names a trusted family source). When trusted, mint
    the CHILD's NESTED belief-world (character_tom's `belief_world` idiom): a
    `trusts` edge child -> source, a nested threat SmEntity carrying `danger=1`
    (`licensed_within_world`, `belief_holder`=addressee) that `character_tom.
    character_belief_world` reads back UNCHANGED, and a nested want-SmEvent for
    the licensed quest (`idx_intentionality`=the WarningLexicon's `licensed_
    response`). The danger-belief is a MODELED object indexed to the child — it
    is NEVER written onto the real (non-nested) addressee entity, so it does not
    leak into the reader's own belief set (the reader's own verdict stays the
    detached hold-open). Untrusted / no addressee -> honest null, nothing
    modeled (the discriminative case)."""
    ensure_seeds(agent)
    addressee = gap.get("addressee")
    threat = gap.get("threat")
    if not addressee or not threat:
        return {"embedded": False, "trusted": None, "gap": gap,
                "reason": ("no addressee vocative -> the warning's SOURCE-trust relation is "
                           "unresolved; nothing modeled (honest null)")}
    tm = trust_membership(agent, addressee)
    if not tm["trusted"]:
        return {"embedded": False, "trusted": False, "trust": tm, "gap": gap,
                "reason": ("the warning's source is %s by the addressee %r -> even WITHIN "
                           "the addressee's belief-world the warning licenses NOTHING; "
                           "nothing modeled" % (tm["polarity"], addressee))}
    sub, native, _ = _resolve(agent)
    child = smr._entity(agent, addressee)               # the belief HOLDER — real, indexed
    # the trusted SOURCE (the addresser of the kin vocative — a parent/warner).
    warner = sub.add_node("WarningSource",
                          {"role": "warner", "kin": 1, "of": addressee,
                           "note": "the addresser of the vocative warning; a source the "
                                   "addressee TRUSTS within its own belief-world",
                           "source": "inference_generation"})
    if not sub.has_edge(child, "trusts", warner):
        smr._edge(native, child, "trusts", warner)      # the CHILD trusts the SOURCE
    # the child's NESTED belief: the named threat is dangerous — LICENSED via trust.
    # (character_tom's belief_world idiom: a fresh nested SmEntity, scoped so it
    #  never collides with the real-world namespace, edged from the holder.)
    scoped = "%s#%s_belief" % (threat, addressee)
    nested = sub.add_node("SmEntity",
                          {"name": scoped, "referent": threat, "nested": 1,
                           "belief_holder": addressee, "flavor": "belief", "danger": 1,
                           "licensed_within_world": 1, "licensed_by": "trusts",
                           "warning_verb": gap.get("verb"), "correct_within_world": 1,
                           "source": "inference_generation"})
    smr._edge(native, child, "belief_world", nested)
    # the child's LICENSED goal WITHIN its world: the quest the believed warning
    # warrants (the WarningLexicon's `licensed_response`). A NESTED want-SmEvent,
    # indexed to the child — the real addressee entity gets NO `goal` attr, so
    # `character_tom.character_goal` still reads None (nothing leaks out).
    remedy = _licensed_response(agent)
    goal_ev = sub.add_node("SmEvent",
                           {"verb": "want", "surface": "implicit_quest", "active": 0,
                            "idx_protagonist": addressee, "idx_intentionality": remedy,
                            "nested": 1, "belief_holder": addressee, "remedy": remedy,
                            "threat": threat, "licensed_within_world": 1,
                            "source": "inference_generation"})
    smr._edge(native, goal_ev, "agent", child)
    smr._edge(native, child, "belief_world", goal_ev)
    return {"embedded": True, "trusted": True, "trust": tm, "gap": gap,
            "addressee": addressee, "threat": threat, "belief_holder": addressee,
            "warner": smr._v(warner), "nested_belief": smr._v(nested),
            "goal_event": smr._v(goal_ev), "remedy": remedy,
            "licensed_within_world": True,
            "danger_belief": {"referent": threat, "danger": 1,
                              "belief_holder": addressee, "licensed": True},
            "note": ("the warning is LICENSED WITHIN the addressee's belief-world (trusted "
                     "source) -> the child correctly believes the danger and the quest is "
                     "warranted; a MODELED object indexed to the child, NOT the reader's own "
                     "belief")}


# --------------------------------------------------------------------------- #
#  PHYSICAL-CAUSAL GAP — two adjacent sentences whose committed verbs form a
#  PHYSICAL-EFFECT pair (drop/pour/add a solid or liquid -> a level rises or
#  overflows) — the displacement inference discourse_coherence's own
#  lexical-cohesion continuity signal cannot see, because the two sentences
#  share NO entity token at all ('pebbles' vs 'water': two distinct referents,
#  linked only by physical world knowledge, never coreference).
# --------------------------------------------------------------------------- #
def detect_causal_gaps(agent, textbase: list) -> list:
    """Every ADJACENT pair of sentences in `textbase` (situation_model_
    reader's own per-sentence predication list — the SAME textbase `detect_
    bridging_gaps` reads, reused, never re-parsed) whose two committed
    predications each carry a relation (verb) — one candidate per adjacent
    pair, keyed on the pair's own lemmatised verbs (`situation_model_reader.
    _lemma`, the SAME WordNet morphy lemmatiser `cos_membership` uses — no
    stemming table, no hardcoded verb list). Returns [{sentence_a, sentence_b,
    i, j, verb_a, verb_b}]; the DECODE (not this scan) decides whether a
    physical schema covers the pair."""
    gaps = []
    n = len(textbase)
    for i in range(n - 1):
        preds_a = textbase[i].get("predications") or []
        preds_b = textbase[i + 1].get("predications") or []
        if not preds_a or not preds_b:
            continue
        verb_a = smr._lemma(str(preds_a[0][0]))
        verb_b = smr._lemma(str(preds_b[0][0]))
        gaps.append({"sentence_a": textbase[i]["sentence"], "sentence_b": textbase[i + 1]["sentence"],
                     "i": i, "j": i + 1, "verb_a": verb_a, "verb_b": verb_b})
    return gaps


def _discourse_event_for(sub, text: str, unit=None):
    for n in sub.nodes("DiscourseEvent"):
        at = sub.node(n)["attrs"]
        if at.get("text") == text and (unit is None or at.get("unit") == unit):
            return n
    return None


def resolve_causal_gap(agent, gap: dict, unit=None) -> dict:
    """Resolve ONE physical-causal gap: decode `[["physical_effect",
    verb_a, verb_b]]` against the codebook; the winning `knowledge_causal`
    schema's `supplies` (`{"relation": "cause"}`) mints BOTH a `coherence_rel`
    edge (relation='cause') and a `causes` edge between the two sentences'
    `DiscourseEvent` nodes, via discourse_coherence's OWN edge-mint primitive
    (`dc._mint_edge`, called AS-IS — the identical edge shape `discourse_
    coherence.read_discourse`'s own cause branch writes) — reused, not
    reimplemented. `discourse_coherence.read_discourse` (also called as-is,
    unmodified) must already have run over this text so the DiscourseEvent
    nodes exist; if it has not, this is an honest DEFERRED null (nothing
    fabricated, nothing silently skipped) rather than a fabricated edge on
    nodes that do not exist yet."""
    dec = decode_gap(agent, [["physical_effect", gap["verb_a"], gap["verb_b"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": gap, "schema": None,
                "reason": ("no physical schema covers %r -> %r -- honest null, "
                           "nothing fabricated") % (gap["verb_a"], gap["verb_b"])}
    sub, native, _ = _resolve(agent)
    coherence = _coherence_of(sub, dec["name"])
    if coherence == "elaborative" and not _is_deep(agent):
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    if supplies.get("relation") != "cause":
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}
    a = _discourse_event_for(sub, gap["sentence_a"], unit=unit)
    b = _discourse_event_for(sub, gap["sentence_b"], unit=unit)
    if a is None or b is None:
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "DiscourseEvent graph not built yet -- discourse_coherence."
                          "read_discourse must run over this text before this resolves "
                          "(deferred, honest -- nothing fabricated on absent nodes)"}
    dc._mint_edge(sub, native, a, b, "coherence_rel", {"relation": "cause",
                                                        "source": "inference_generation",
                                                        "schema": dec["name"]})
    dc._mint_edge(sub, native, a, b, "causes")
    return {"minted": True, "gap": gap, "schema": dec["name"], "supplies": supplies,
            "effect": {"a": smr._v(a), "b": smr._v(b)}}


def read_and_infer_causal(agent, text: str, *, window: int = 2) -> dict:
    """A SECOND whole-text driver, alongside `read_and_infer`: builds the
    spine (`situation_model_reader.read_into_situation_model`, UNCHANGED) AND
    the discourse graph (`discourse_coherence.read_discourse`, UNCHANGED,
    called as-is) IN THE CORRECT DEPENDENCY ORDER — the DiscourseEvent graph
    must exist before the deeper physical-causal pass can decide a link
    discourse_coherence's own lexical-cohesion signal cannot see — then
    detects + resolves every physical-causal gap. This is the SAME kind of
    top-level driver `read_and_infer` already is; it is the NORMAL read path
    for a caller who wants both layers. `scripts/jabberwock_reads_the_crow.py`
    does not exercise this driver: per its own documented INTEGRATION NOTE it
    calls `discourse_coherence.read_discourse` AFTER inference_generation's
    gap passes (an ordering fixed by that frozen script, which this module
    cannot reach into without editing either frozen file) — an honest,
    reported limitation of THAT harness's call order, not of this mechanism
    (see the module-level report accompanying this change)."""
    ensure_seeds(agent)
    spine = smr.read_into_situation_model(agent, text)
    dc.ensure_codebook(agent)
    discourse = dc.read_discourse(agent, text, window=window)
    gaps = detect_causal_gaps(agent, spine["textbase"])
    resolved = [resolve_causal_gap(agent, g) for g in gaps]
    return {"text": text, "spine": spine, "discourse": discourse,
            "causal_gaps": gaps, "causal": resolved}


# --------------------------------------------------------------------------- #
#  ELABORATIVE CANDIDATES — every resident entity, gated by coherence depth.
# --------------------------------------------------------------------------- #
def detect_elaborative_candidates(agent, unit=None) -> list:
    sub, _, _ = _resolve(agent)
    return [{"entity": at.get("name"), "node": n}
            for n in sub.nodes("SmEntity")
            for at in [sub.node(n)["attrs"]] if at.get("name")
            if unit is None or at.get("unit") == unit]


# --------------------------------------------------------------------------- #
#  LOGICAL / PROPOSITIONAL-DEDUCTION GAP — genuine modus ponens: an entity
#  ALREADY carries a fully-stated antecedent fact (attr==1) whose held
#  `knowledge_logical` implication's consequent has not yet been drawn. See
#  docs/research/engine_substrate/DEDUCTION_GENERALIZATION_PREREG.md §3 for why
#  this is NOT `detect_precondition_gaps`'s "exactly one conjunct away from N"
#  shape: a single-antecedent implication has no PARTIAL state — the
#  antecedent is either fully stated or not — so there is nothing to be "one
#  conjunct short" of. Instead this mirrors `detect_goal_gaps`'s BREADTH-OFFER
#  discipline (its own docstring: "this scan never hardcodes which attr NAME
#  counts as a need-state... the codebook is what actually recognises one"):
#  every resident attr==1 fact is offered as a candidate ANTECEDENT, and the
#  DECODE (not this scan) decides which ones a held `knowledge_logical`
#  ShapeSignature actually covers. domains/propositional_deduction.py mints
#  those schemas (from prose or hand-seeded in seeds/inference_logical.json);
#  this module never inspects a schema's content, only its decode outcome.
# --------------------------------------------------------------------------- #
def detect_implication_gaps(agent, unit=None) -> list:
    """Every resident, non-nested SmEntity's stated fact (any attr==1,
    excluding coref bookkeeping / goal / name — the SAME `_NON_CANDIDATE_*`
    exclusion `detect_goal_gaps` uses) offered as a candidate ANTECEDENT for a
    held propositional implication. Returns [{entity, node,
    antecedent_attr}]."""
    ensure_logical_seeds(agent)
    sub, _, _ = _resolve(agent)
    gaps = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        name = at.get("name")
        if unit is not None and at.get("unit") != unit:
            continue
        if not name or at.get("nested"):
            continue
        for k, v in at.items():
            if v != 1 or k in _NON_CANDIDATE_KEYS or k.startswith(_NON_CANDIDATE_PREFIXES):
                continue
            gaps.append({"entity": name, "node": n, "antecedent_attr": k})
    return gaps


def resolve_implication_gap(agent, gap: dict, *, t: int = 0, unit=None) -> dict:
    """Resolve ONE logical/propositional-deduction gap: decode `[["holds",
    antecedent_attr]]` against the codebook (the SAME pool, the SAME
    `decode_gap` -> `ShapeDecode` -> `reading_collapse._winner` collapse every
    other gap kind uses — REUSING the general pipeline's best-fit selection
    rather than reimplementing `ground_reductions.GroundedReduction.compute`'s
    bespoke ordered-clause loop, per DEDUCTION_GENERALIZATION_PREREG.md §4).
    The winning `knowledge_logical` schema's `supplies`
    (`{"relation": "is_a", "attr": ...}`) — BYTE-IDENTICAL in shape to
    `knowledge_enabling`'s `supplies` — is minted via `situation_model_reader.
    ingest_predication`, the IDENTICAL call `resolve_precondition_gap` already
    makes: UNCHANGED, reused as-is, so a derived consequent that itself
    completes ANOTHER stalled rule cascades through the SAME fixpoint with no
    new code. Idempotent (mirrors `resolve_elaborative_candidate`'s own
    already-holds check): a consequent already held is not re-derived. No
    covering schema -> honest null, nothing fabricated."""
    dec = decode_gap(agent, [["holds", gap["antecedent_attr"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": gap, "schema": None,
                "reason": ("no knowledge_logical schema holds an implication for "
                           "%r -- honest null, nothing fabricated") % gap["antecedent_attr"]}
    sub, _, _ = _resolve(agent)
    coherence = _coherence_of(sub, dec["name"])
    if coherence == "elaborative" and not _is_deep(agent):
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    if supplies.get("relation") == "is_a" and supplies.get("attr"):
        ent = smr._entity(agent, gap["entity"], unit=unit)
        if sub.node(ent)["attrs"].get(supplies["attr"]) == 1:
            return {"minted": False, "gap": gap, "schema": dec["name"],
                    "reason": "already holds -- idempotent, no re-mint"}
        ing = smr.ingest_predication(agent, ["is_a", gap["entity"], supplies["attr"]],
                                     t=t, unit=unit)
        return {"minted": True, "gap": gap, "schema": dec["name"], "supplies": supplies,
                "ingest": ing}
    return {"minted": False, "gap": gap, "schema": dec["name"],
            "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}


# --------------------------------------------------------------------------- #
#  DECODE — the collapse. Goal -> ShapeDecode -> the winning schema.
# --------------------------------------------------------------------------- #
def _schema_node(sub, name: str):
    for n in sub.nodes("ShapeSignature"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def decode_gap(agent, goal: list) -> dict:
    """DECODE one gap's goal relation-system against the held knowledge
    codebook (every ShapeSignature node — the SAME Rust ShapeDecode Term
    `reading_collapse.py` uses). The WINNER is read off the decode's own
    ranking via `reading_collapse._winner` (reused, not reimplemented) —
    the schema (or None) the collapse itself chose. Returns {name, fit,
    result}."""
    sub, _, _ = _resolve(agent)
    ensure_seeds(agent)
    res = rf.compose_design_for_goal(sub, goal, beam=3, max_steps=4, cand_k=6)
    name, fit = rc._winner(res)
    return {"name": name, "fit": fit, "result": res}


# --------------------------------------------------------------------------- #
#  MINT — the winning schema's OWN `supplies` data names the fact to write.
# --------------------------------------------------------------------------- #
def _supplies_of(sub, schema_name: str) -> dict:
    node = _schema_node(sub, schema_name)
    if node is None:
        return {}
    try:
        return json.loads(sub.node(node)["attrs"].get("supplies") or "{}")
    except Exception:
        return {}


def _coherence_of(sub, schema_name: str) -> str:
    node = _schema_node(sub, schema_name)
    return (sub.node(node)["attrs"].get("coherence") if node is not None else "blocking") or "blocking"


def _mint_part_of(agent, entity_name: str, whole_name: str, unit=None) -> dict:
    """Mechanical mint: a `part_of` edge from the bridged entity to the
    whole the winning schema named — the SAME admissibility-gated write
    idiom `reading_collapse._write_predications` uses (try `add_edge`, fall
    back to `add_edge_unchecked` flagged `gated=0`), since `part_of` is not
    a change-of-state verb `situation_model_reader.ingest_predication`
    would otherwise mint."""
    sub, native, _ = _resolve(agent)
    e = smr._entity(agent, entity_name, unit=unit)
    w = smr._entity(agent, whole_name, unit=unit)
    if not sub.has_edge(e, "part_of", w):
        try:
            sub.add_edge(e, "part_of", w, {"source": "inference_generation", "bridged": 1})
        except Exception:
            smr._edge(native, e, "part_of", w)
    native.run_rules(10000)
    return {"entity": entity_name, "whole": whole_name}


def resolve_precondition_gap(agent, gap: dict, *, t: int = 0, unit=None) -> dict:
    """Resolve ONE world-knowledge gap: decode `[["needs", entity,
    need_attr]]` against the codebook; the winning `knowledge_enabling`
    schema's `supplies` (an is_a fact) is minted via
    `situation_model_reader.ingest_predication` — UNCHANGED, reused as-is,
    so its own property-predication branch sets the attr AND re-runs
    `run_rules`, completing the stalled chain. No covering schema -> honest
    null, nothing minted (the discriminative case)."""
    dec = decode_gap(agent, [["needs", gap["entity"], gap["need_attr"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": gap, "schema": None,
                "reason": ("no knowledge schema covers %r needing %r -- honest null, "
                           "nothing fabricated") % (gap["entity"], gap["need_attr"])}
    sub, _, _ = _resolve(agent)
    coherence = _coherence_of(sub, dec["name"])
    if coherence == "elaborative" and not _is_deep(agent):
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    if supplies.get("relation") == "is_a" and supplies.get("attr"):
        ing = smr.ingest_predication(agent, ["is_a", gap["entity"], supplies["attr"]], t=t,
                                     unit=unit)
        # ADDITIVE DURABLE MARKER (blackboard dissolution): the enabling-
        # condition fact was a PRECONDITION GAP the text left unfilled (the
        # direct route was genuinely blocked), not a stated property. The is_a
        # mint alone is indistinguishable from a stated property, so stamp a
        # distinct `blocked_gap` marker on the entity's SmEntity node -- this
        # is what trope_theme's BLOCKED signal reads (graph-native), replacing
        # the transient `graph['blocking']` record. Semantics of the is_a attr
        # are untouched.
        node = gap.get("node")
        if node is not None:
            try:
                sub.set_attr(node, "blocked_gap", 1)
            except Exception:
                pass
        return {"minted": True, "gap": gap, "schema": dec["name"], "supplies": supplies,
                "ingest": ing}
    return {"minted": False, "gap": gap, "schema": dec["name"],
            "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}


def resolve_bridging_gap(agent, gap: dict, unit=None) -> dict:
    """Resolve ONE bridging gap: decode `[["needs_whole", entity]]` against
    the codebook; the winning `knowledge_partwhole` schema's `supplies`
    names the whole -> mint the `part_of` edge. No lexical cue was used to
    find the whole — the gap (a definite with no antecedent) triggered the
    search; the codebook (world knowledge) supplied the target."""
    dec = decode_gap(agent, [["needs_whole", gap["entity"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": gap, "schema": None,
                "reason": "no knowledge schema names a whole for %r -- honest null" % gap["entity"]}
    sub, _, _ = _resolve(agent)
    coherence = _coherence_of(sub, dec["name"])
    if coherence == "elaborative" and not _is_deep(agent):
        return {"minted": False, "gap": gap, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    if supplies.get("relation") == "part_of" and supplies.get("object"):
        eff = _mint_part_of(agent, gap["entity"], supplies["object"], unit=unit)
        return {"minted": True, "gap": gap, "schema": dec["name"], "supplies": supplies,
                "effect": eff}
    return {"minted": False, "gap": gap, "schema": dec["name"],
            "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}


def resolve_elaborative_candidate(agent, cand: dict, *, t: int = 0) -> dict:
    """Resolve ONE elaborative candidate (any resident entity — no rule
    needs this fact, it is offered purely for depth): decode `[["elaborate",
    entity]]`; only a schema tagged `coherence:"elaborative"` can win here
    (the codebook's `knowledge_enabling`/`knowledge_partwhole` schemas never
    use the "elaborate" predicate), and it only MINTS under a DEEP
    standard_of_coherence."""
    dec = decode_gap(agent, [["elaborate", cand["entity"]]])
    if dec["name"] is None or dec["fit"] <= 0:
        return {"minted": False, "gap": cand, "schema": None,
                "reason": "no elaborative schema knows more about %r" % cand["entity"]}
    sub, _, _ = _resolve(agent)
    if not _is_deep(agent):
        return {"minted": False, "gap": cand, "schema": dec["name"],
                "reason": "elaborative schema, standard_of_coherence is shallow -- not fired"}
    supplies = _supplies_of(sub, dec["name"])
    at = sub.node(cand["node"])["attrs"]
    if supplies.get("attr") and at.get(supplies["attr"]) == 1:
        return {"minted": False, "gap": cand, "schema": dec["name"],
                "reason": "already holds -- idempotent, no re-mint"}
    if supplies.get("relation") == "is_a" and supplies.get("attr"):
        ing = smr.ingest_predication(agent, ["is_a", cand["entity"], supplies["attr"]], t=t)
        return {"minted": True, "gap": cand, "schema": dec["name"], "supplies": supplies,
                "ingest": ing}
    return {"minted": False, "gap": cand, "schema": dec["name"],
            "reason": "winning schema supplies an unrecognised relation %r" % (supplies,)}


# --------------------------------------------------------------------------- #
#  THE DRIVER — read the spine, then generate the unstated inferences.
# --------------------------------------------------------------------------- #
def _situation_model(sub) -> dict:
    model: dict = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if nm:
            model[nm] = {k: v for k, v in at.items() if k != "name"}
    return model


def read_and_infer(agent, text: str, *, max_sentences: int = 40) -> dict:
    """THE WIRE for step 3. Read `text` into the situation model (the
    UNCHANGED spine, situation_model_reader.read_into_situation_model),
    snapshot its BEFORE state, then generate the unstated inferences:

      1. every stalled world-knowledge precondition gap -> decode -> mint
         (always; `coherence:"blocking"`);
      2. every bridging gap (definite, no antecedent) -> decode -> mint
         (always; `coherence:"blocking"`);
      3. every resident entity as an elaborative candidate -> decode -> mint
         ONLY under a deep standard_of_coherence.

    Returns {text, before_situation_model, blocking, bridging, elaborative,
    situation_model} — the AFTER state includes what was never stated."""
    ensure_seeds(agent)
    spine = smr.read_into_situation_model(agent, text, max_sentences=max_sentences)
    sub, _, _ = _resolve(agent)
    before = {k: dict(v) for k, v in spine["situation_model"].items()}

    blocking = [resolve_precondition_gap(agent, g, t=900 + i)
                for i, g in enumerate(detect_precondition_gaps(agent))]
    bridging = [resolve_bridging_gap(agent, g)
                for g in detect_bridging_gaps(agent, spine["textbase"])]
    goal = [resolve_goal_gap(agent, g) for g in detect_goal_gaps(agent)]
    # THE LICENSING DISTINCTION: an imperative warning ('Beware X') with no
    # governing felt need is HELD OPEN, not collapsed into a goal (the
    # Jabberwocky correction). Runs AFTER the goal pass so a warning grounded in
    # an established need is already inferred and records nothing new.
    warning_gaps = detect_warning_gaps(agent, spine["textbase"])
    warning = [resolve_warning_gap(agent, g) for g in warning_gaps]
    elaborative = [resolve_elaborative_candidate(agent, c, t=950 + i)
                   for i, c in enumerate(detect_elaborative_candidates(agent))]
    # STANCE-RELATIVE: the SAME warning held open as OBJECTIVE FACT above is
    # LICENSED WITHIN the addressee's belief-world when the source is trusted.
    # ADDITIVE + decoupled: mints a NESTED (belief_holder-indexed) danger-belief,
    # never an OpenGoal/Ambiguity and never a leak onto the real addressee — so
    # the detached hold-open (task 101) is byte-identical.
    embedded = [resolve_warning_embedded(agent, g) for g in warning_gaps]
    # GENUINE MODUS PONENS: every stated fact offered as a candidate antecedent
    # for a held knowledge_logical implication (DEDUCTION_GENERALIZATION_
    # PREREG.md/_RESULTS.md). Runs AFTER the other passes so a fact minted by
    # an earlier pass (fragile/goal/...) is ALSO available as an antecedent —
    # additive: `logical` is a NEW dict key, nothing above depends on it.
    logical = [resolve_implication_gap(agent, g, t=980 + i)
               for i, g in enumerate(detect_implication_gaps(agent))]

    return {"text": text, "textbase": spine["textbase"], "before_situation_model": before,
            "blocking": blocking, "bridging": bridging, "goal": goal, "warning": warning,
            "embedded": embedded, "logical": logical,
            "elaborative": elaborative, "situation_model": _situation_model(sub)}


__all__ = [
    "ensure_seeds", "ensure_logical_seeds", "coherence_depth", "set_coherence_depth",
    "detect_precondition_gaps", "detect_bridging_gaps", "detect_goal_gaps",
    "detect_causal_gaps", "detect_elaborative_candidates", "detect_implication_gaps",
    "detect_warning_gaps", "warning_membership", "resolve_warning_gap",
    "trust_membership", "resolve_warning_embedded",
    "decode_gap", "resolve_precondition_gap", "resolve_bridging_gap", "resolve_goal_gap",
    "resolve_causal_gap", "resolve_elaborative_candidate", "resolve_implication_gap",
    "read_and_infer", "read_and_infer_causal",
]

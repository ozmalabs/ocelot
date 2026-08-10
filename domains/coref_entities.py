"""coref_entities — WIRES coreference resolution into the READING path.

situation_model_reader.py builds a SITUATION MODEL (SmEntity / SmEvent) from
read text, but it is coreference-BLIND: a pronoun argument ("he", "she", "it",
"they") mints its OWN literal SmEntity ("he") instead of resolving to the
protagonist it denotes ("john"), so a state change attributed to "he" lands on
a throwaway node, not the real protagonist. domains/reference_resolution.py
already HAS a real resolver (Centering Theory Cf/Cb, the Givenness Hierarchy,
agreement filtering) — but it is wired only to the CONVERSATION path
(ConversationWorld's frame-shaped turns + a `world._concept_nodes` index), not
to reading, and its "decisions" module is imported here.

STUDY FINDING (graph-native source audit). reference_resolution.py's antecedent
RANKING is *not* graph-native: `reference_resolution_procedure` ranks survivors
with a Python `max(survivors, key=lambda ...)` (salience_factors) and an `if
cb_survivor is not None` branch (centering_rule_1) — a Python picker reading
graph-resident attrs. Its STATE SHAPE (a `frame` dict with grammatical-role
slots, a `world._concept_nodes` index) is also conversation-specific and does
not transplant onto SmEntity / [rel, arg0, arg1] triples. So this module does
NOT import DiscourseStore; it REUSES reference_resolution's DATA (`_CF_RANK`,
`_PRONOUNS` — the cf_ranking table and the closed-class pronoun agreement
specs, imported directly, not re-typed) and its DOCUMENTED ALGORITHM (form
licensing -> agreement filter -> centering_rule_1-or-salience -> bind), but
RE-EXPRESSES THE RANKING AS A GRAPH PROGRAM: an `Argmax` Term-tree over the
resident `SmEntity` pool, evaluated by `substrate.evaluate` (native Rust) —
the same discipline domains/native_vote.py used to migrate a Python
`Counter.most_common` decision into a graph-native `Argmax`. Python never
calls `max()`/`sorted()` to pick a winner; the DSL evaluator does.

RESONANCE / THE BUFFER. Myers & O'Brien 1998 resonance = a probe (the pronoun)
activates every resident representation in parallel; the most active wins
(integration). The natural resonance substrate here is the SmEntity pool
itself — situation_model_reader already keeps SmEntity nodes RESIDENT across
sentence boundaries (the situation model IS the cross-sentence memory), which
is exactly the persistence reading_scope.py's RetainedTrace buffer provides
for SEGMENTATION alternatives, one level down. This module does not force a
literal RetainedTrace node onto entities (that node type carries segmentation
lattices, a different concern) — it rides the SAME persistence pattern
(salience-ranked resident nodes; a query re-activates the highest-scoring one)
directly on SmEntity, which is the natural place for it.

RI-Val VALIDATION (reading_review's licensing discipline, applied here): a
bind that does not clear a MARGIN over its runner-up is HELD OPEN (a Mention
node flagged `held_open=1`, no `refers_to` edge), never force-bound. The
margin check + Cf/Cb turn bookkeeping are ADAPTER STATE (recording what was
said, the same status as `recency`/`mentions` attrs) — the sole DECISION is
the antecedent-choosing Argmax.

WHAT PYTHON DOES HERE (mechanical adapter I/O):
  * grounds category/number features per entity ONCE at first mention (reusing
    the held `dictionary_lexicon` faculty reading_review already relies on) —
    a proper-noun surface (capitalized in source) is left "unknown" rather than
    trusting a common-noun WordNet sense (WordNet's most frequent noun sense
    for 'john'/'bill' is a common NOUN — toilet / legislative bill — not the
    person named; this is the SAME honest "gender not grounded" stance
    reference_resolution.py documents, extended to proper-name category);
  * builds + evaluates the Argmax Term (the decision);
  * writes the `Mention --refers_to--> SmEntity` edge (or the `held_open` flag);
  * substitutes a BOUND pronoun argument with its antecedent's name before
    handing the predication to situation_model_reader.ingest_predication
    (UNCHANGED, reused as-is) so the state change lands on the resolved
    protagonist, not a throwaway "he" node.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import gender_shape as gs
from domains import reading_collapse as rc
from domains import reading_scope as rs
from domains import situation_model_reader as smr
from domains.reference_resolution import _CF_RANK, _DEIXIS, _PRONOUNS

# situation_model_reader's role vocabulary (agent / theme / goal) mapped onto
# reference_resolution's cf_ranking (subject > object > other) — REUSED table,
# not a new numeric scheme. "theme" (the direct-object-shaped argument) ranks
# as patient; "goal" (a motion verb's locative complement) ranks as location
# (an oblique, lower-salience complement).
_ROLE_RANK = {
    "agent": _CF_RANK["agent"],
    "theme": _CF_RANK["patient"],
    "goal": _CF_RANK["location"],
}
_DEFAULT_ROLE_RANK = 99.0

# Score weights (native_vote.py's BIG*primary - secondary convention): a
# CLEAN candidate outranks a junk blob no matter what (a blob's apparent
# centering/recency signal is itself an artefact of the mis-parse that minted
# it, not a genuine discourse fact), so CLEAN_BONUS sits ABOVE the Cb bonus,
# which dominates recency, which dominates the role-rank tie-break. All
# components are integers/turn-counts/0-1 flags in practice, so the only
# possible margins between two candidates are 0 (a genuine tie) or >= 1 (some
# distinguishing signal) — MARGIN_EPS sits strictly between them.
_CLEAN_BONUS = 100_000_000.0
_CB_BONUS = 1_000_000.0
_RECENCY_W = 100.0
_MARGIN_EPS = 0.5
_NO_CB_SENTINEL = "__no_cb__"          # never matches a real entity name

# --------------------------------------------------------------------------- #
#  REVISABLE FEATURE BELIEFS — tuning for the surprise -> explanation collapse.
#  A feature belief is NOT a fact and NOT a majority vote: it is a held value
#  with a SOURCE and a CONFIDENCE. A conflicting observation is a SURPRISE, and
#  a `keep` null competes with `reader_wrong` / `writer_wrong` / `character_wrong`
#  / `referent_changed` in a native Argmax. `reader_wrong` beats `keep` only when
#  the held belief is a WEAK reader-inference AND the accumulated conflicting
#  evidence outweighs it — so a strong (definitional) or well-supported belief is
#  never lightly overturned (protects the bench), while a stray low-confidence
#  bind (the mis-gendered sparrow) is revised once its own pronouns pile up.
# --------------------------------------------------------------------------- #
# A belief is CONTESTED when its accumulated conflicting observations reach a
# meaningful fraction of the observations that SUPPORT it. `keep` (the null) grows
# with SUPPORT -- the count of consistent observations -- so a well-supported
# belief (carter, "he" 12x) resists; `reader_wrong` earns _SURPRISE_EV_W per
# accumulated CONFLICT. Revision fires when SURPRISE_EV·conflicts > support + floor,
# i.e. conflicts exceed ~(support/SURPRISE_EV): a strong SALIENT-MINORITY of
# contesting evidence, NOT a strict majority (conflicts never need to exceed
# support) -- the user's "it's a salience item, not a majority". This is robust to
# the initial bind's margin (which, once Binding Principle B removes the easy
# object=subject mis-binds, no longer tracks correctness): the mis-gendered
# sparrow (conflict 3 vs support 5) revises; the correctly-male carter (conflict 4
# vs support 12) and every definitional prior (source != reader_inference -> the
# reader_wrong arm scores 0) do not.
_BELIEF_STRONG_CONF = _CLEAN_BONUS   # definitional / word-dequant prior: immovable
_KEEP_BASE = 0.5               # the null explanation's floor -- revise only if beaten
# Confidence enters `keep` at a TINY weight: it only matters when it is STRUCTURAL
# -- a bind won by a cleanliness/centering gulf (margin >= _CB_BONUS ~1e6, e.g. the
# sole candidate in a pool -> margin ~1e18) is a well-founded belief and 0.001·conf
# swamps any conflict; a bind won by mere RECENCY (margin in the 100s, the sparrow's
# stray 'him') gives 0.001·conf < 1, so it does NOT protect and the belief stays
# revisable by contested evidence. The boundary (conf ~ a few·1e3) sits cleanly
# between the recency scale (1e2) and the structural scale (1e6).
_KEEP_CONF_W = 0.001           # only STRUCTURAL confidence (CB/clean gulf) protects
_KEEP_SUPPORT_W = 1.0          # the accumulated consistent SUPPORT is the main keep
_REVISE_CONF_W = 0.0           # reader_wrong is not damped by the initial margin ...
_REVISE_SUPPORT_W = 0.0        # ... nor by support directly (keep carries support)
_SURPRISE_EV_W = 2.5           # evidence weight per accumulated conflicting demand
_SOURCE_READER = "reader_inference"
_SOURCE_DEFINITIONAL = "definitional_prior"
_SOURCE_WRITER = "writer_assertion"
_SOURCE_CHARACTER = "character_assertion"
_EXPLANATIONS = ("keep", "reader_wrong", "writer_wrong",
                 "character_wrong", "referent_changed")

# ANIMATE-PROTAGONIST preference. This lives at the PARSE layer, not the coref score.
# The mis-ID the task names ('left'/'went' binding 'foe' because WordNet grounds
# 'foe'->enemy->person) is an ARGUMENT-STRUCTURE fact: in 'the manxome foe he sought'
# / 'He left it dead' / 'He went galumphing back' the ANIMATE agent IS the pronoun
# subject 'he' (bound by case, OSV/SVO -- see reading_collapse._event_predication) and
# 'foe' is the OBJECT, so it never enters the agent slot. Fixing the PARSE (the finite
# main verb + inverted role binding) makes 'he' the protagonist of left/went/sought
# directly, and the existing metrical-prominence factor binds that 'he' to the ONE
# licensed hero -- so 'foe' is never the antecedent. An ANIMACY *score* factor was
# tried here and REVERTED: it perturbed the crow's coref (a lowercase animate common
# noun re-ranked over a competitor), breaking the byte-identity guard. The animate
# preference is therefore expressed where it is decisive and non-regressing -- in the
# argument structure -- not as a coref tie-breaker.

# METRICAL PROMINENCE (the PINCER — M2). In metrical VERSE the salient referent
# is the metrically-prominent AGENT: the entity that is the subject of a clause
# whose action verb sits on the strong beat (the ictus), read off the SAME
# temporal-harmonic scan metrical_reading uses. A pronoun-only hero ('He took
# his vorpal sword') has no proper-noun anchor, so the flat salience/recency
# ranking mislabels it as the salient-but-wrong first-antecedent ('mimsy'). The
# prominence FACTOR licenses the hero over that antecedent. It sits ABOVE
# CLEAN_BONUS so a metrically-licensed protagonist outranks a recency artefact.
#
# BYTE-IDENTITY GUARD: this factor is an IfThenElse that yields EXACTLY 0.0 for
# any entity whose `coref_metrical_prominence` attr is not 1.0 — missing OR 0.0
# both give 0.0 (robust to the Times-skips-None evaluator behaviour). Prominence
# is set to 1.0 ONLY inside a VERSE text (newline-delimited, metrically
# confident); PROSE (the crow — zero newlines, no confident meter) never sets
# it, so every prose candidate contributes 0.0 and the Argmax is unchanged.
_METRICAL_PROM_W = 10_000_000_000.0
_PROMINENT = 1.0

# STORY-LEVEL SALIENCE (the SALIENT ORDER-N CACHE — M3). A pronoun's salient
# referent 50 sentences later is the entity the cache PROMOTED to story-level
# working memory (domains/salient_cache.py: a protagonist recurring across a
# wide span rises to story salience; a one-scene bystander decays at the local
# level and never promotes). The promote RULE mirrors that story salience onto
# the SmEntity as `coref_story_salience` (+ the `coref_story_salience_on` flag);
# this FACTOR reads it, so the coref Argmax binds a pronoun to the MOST-SALIENT
# compatible entity in the cache — long-form coreference, decided graph-natively.
#
# PLACEMENT: story-salience sits ABOVE the Cb centering bonus but BELOW the
# cleanliness junk-filter — so among CLEAN candidates the entity the working
# memory holds at story level wins, and Centering (the backward-looking center)
# FALLS OUT as the degenerate case (when nothing is promoted, the pre-M3 Cb +
# recency ranking is exactly what remains). SCALE: coref_story_salience is a
# small mention count (~3-30) and a promoted entity has >= 3; W*3 > _CB_BONUS and
# W*max stays below _CLEAN_BONUS, so a promoted character always outranks the
# local Cb yet never overrides the clean/junk gate.
#
# BYTE-IDENTITY GUARD: an IfThenElse yielding EXACTLY 0.0 for any entity whose
# `coref_story_salience_on` attr is not 1.0 (missing OR 0.0 both give 0.0 — the
# IfThenElse is robust to the Times-skips-None evaluator behaviour, mirroring
# is_prominent). The flag is set ONLY by the salient_cache promote rule, which
# only fires when the cache is INSTALLED (a long-form read opts in) AND an entity
# persists across a wide span. A short fable (the crow — cache absent, or too
# short to promote) never sets it, so every candidate contributes 0.0 and the
# Argmax is byte-identical.
_STORY_SALIENCE_W = 1_000_000.0

# CONTENT-OVER-PRONOUN antecedent preference (the animal-hero UNBLOCK, second
# half). Gender agreement makes the animal hero COMPATIBLE, but in a long tale a
# discourse-initial 'he' that held open mints a throwaway pronoun-surface SmEntity
# ('he'), which then out-competes the real named referent (the ass) on RECENCY and
# intercepts every later 'he' — so the ass's he/the-ass never merge. This is the
# well-established coref principle that a pronoun binds a CONTENT antecedent over
# another PRONOUN when both are compatible. A graph-native FACTOR (like cleanliness):
# a candidate whose name is a CLOSED-CLASS FUNCTION WORD (coref_function_word == 1.0)
# is dispreferred by a penalty that dominates recency + story-salience but sits BELOW
# the cleanliness junk-gate — so a clean content referent always beats a pronoun-
# surface entity, yet a function-word entity is STILL bound when it is the only
# compatible candidate (a genuine discourse-initial pronoun: test_cross_sentence_
# repeated). coref_function_word is grounded ONCE at first mention off the SAME
# closed-class faculty narrative_structure._is_function_word reads; a content noun
# (crow/ass/dog/robbers) is 0.0, so the crow pool — which never mints a competing
# pronoun-surface entity — is byte-identical (every candidate contributes 0.0).
_FUNCTION_WORD_PENALTY = 50_000_000.0


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O — the same idiom every domains/*.py uses).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


# --------------------------------------------------------------------------- #
#  Term constructors — raw-dict, the SAME convention native_vote.py / abs_read.py
#  use: a Python dict shaped exactly like the Rust `TermNode` JSON, handed to
#  `native.evaluate(term, env)` (runners/dsl/src/py.rs `fn evaluate`, which
#  parses + evaluates the Term IN RUST — genuinely native, not the pure-Python
#  substrate/dsl.py evaluator some legacy adapters use).
# --------------------------------------------------------------------------- #
def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def _Not(a):
    return {"type": "Not", "arg": a}


def _And(items):
    return {"type": "And", "items": items}


def _Or(items):
    return {"type": "Or", "items": items}


def _Neg(a):
    return {"type": "Neg", "arg": a}


def _Plus(items):
    return {"type": "Plus", "items": items}


def _Times(items):
    return {"type": "Times", "items": items}


def _IfThenElse(c, t, o):
    return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def _Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def _Argmax(src, var, val):
    return {"type": "Argmax", "source": src, "var_name": var, "value": val,
            "default": None}


def _MaxOver(src, var, val, default=None):
    return {"type": "MaxOver", "source": src, "var_name": var, "value": val,
            "default": default}


def _NodesOfType(t):
    return {"type": "NodesOfType", "node_type": t}


def _entity_set():
    """Every resident SmEntity — the resonance pool a pronoun probes."""
    return _NodesOfType("SmEntity")


def _agreement_term(var: str, spec: dict) -> dict:
    """form_status_licensing + agreement_filter, AS A TERM: number + the GENDER
    SHAPE-MATCH.

    GENDER AS A DECODED SHAPE (not a table). A person-pronoun ('he'/'she') no
    longer filters to a fixed {person, unknown} category set — it matches the
    entity's decoded gender SHAPE:

      · ANIMATE — the entity can be a character that takes a gendered pronoun.
        The old person/unknown admittance is PRESERVED EXACTLY (explicit category
        Eq's, robust to a missing coref_animate attr — byte-identity) and EXTENDED
        with `animal` category + `coref_animate == 1.0` (a whole-animal word).
        This is what makes an ANIMAL HERO compatible: the ass, mis-grounded
        `object` by its buttocks sense-1 yet carrying ass.n.03 (a donkey), is
        animate, so 'he' can bind it.
      · GENDER-COMPATIBLE — PERMISSIVE while the gender is UNDERSPECIFIED (missing
        / "" / "unknown" all pass `Not(Eq(gender, opposite))`), STRICT once it has
        been established (a male entity rejects 'she', a female entity rejects
        'he'). The decoded/established gender lives in the `coref_gender` attr; the
        pronoun's own gender is `spec['gender']` (its lexical shape). Absent a
        gender in the spec (possessive resolvers, raw-spec test calls), the gender
        overlay is omitted and only animacy gates.

    'it' (non_person) and 'they' (any) are UNCHANGED — number/non-person alone."""
    conds = []
    if spec["number"] == "plural":
        conds.append(_Eq(_Attr(_V(var), "coref_number"), _Lit("plural")))
    elif spec["number"] == "singular":
        conds.append(_Not(_Eq(_Attr(_V(var), "coref_number"), _Lit("plural"))))
    agree = spec["agree"]
    if agree == "person":
        animate = _Or([
            _Eq(_Attr(_V(var), "coref_category"), _Lit("person")),
            # `unknown` still admits (byte-id: robust to a missing coref_animate),
            # UNLESS animacy was explicitly demoted to 0.0 — a non-nominal glom the
            # parser nounified ('asleep'), which is not an animate referent.
            _And([_Eq(_Attr(_V(var), "coref_category"), _Lit("unknown")),
                  _Not(_Eq(_Attr(_V(var), "coref_animate"), _Lit(0.0)))]),
            _Eq(_Attr(_V(var), "coref_category"), _Lit("animal")),
            _Eq(_Attr(_V(var), "coref_animate"), _Lit(1.0)),
        ])
        gender = spec.get("gender")
        if gender:
            opp = gs.opposite_gender(gender)
            conds.append(_And([
                animate,
                _Not(_Eq(_Attr(_V(var), "coref_gender"), _Lit(opp))),
            ]))
        else:
            conds.append(animate)
    elif agree == "non_person":
        conds.append(_Not(_Eq(_Attr(_V(var), "coref_category"), _Lit("person"))))
    # agree == "any" (they/them): number alone gates it.
    if not conds:
        return _Lit(True)
    return conds[0] if len(conds) == 1 else _And(conds)


def _score_term(var: str, cb_name: Optional[str]) -> dict:
    """CLEANLINESS (a groundable-nominal candidate beats a junk blob, always)
    + centering_rule_1 (Cb bonus) + salience_factors (recency, then
    cf_ranking via the stored role-rank) — ONE composite score, the Argmax's
    `value`. Cleanliness is read off the SAME `coref_cleanliness` graph attr
    every other factor here reads its own stored attr from — a factor in the
    ranking, not a Python winner-pick."""
    is_cb = _IfThenElse(
        _Eq(_Attr(_V(var), "name"), _Lit(cb_name or _NO_CB_SENTINEL)),
        _Lit(1.0), _Lit(0.0))
    # METRICAL PROMINENCE — a graph-native FACTOR, not a Python override: the
    # metrically-licensed protagonist (coref_metrical_prominence == 1.0) outranks
    # a recency/cleanliness artefact. Yields 0.0 for every non-prominent (missing
    # or 0.0) candidate, so a PROSE pool (no entity ever prominent) is byte-
    # identical to the pre-M2 term. Mirrors the is_cb IfThenElse shape.
    is_prominent = _IfThenElse(
        _Eq(_Attr(_V(var), "coref_metrical_prominence"), _Lit(_PROMINENT)),
        _Lit(_METRICAL_PROM_W), _Lit(0.0))
    # STORY-LEVEL SALIENCE (the salient order-N cache) — a graph-native FACTOR,
    # 0.0 for every entity the cache did not promote (flag missing OR 0.0), so a
    # short-text / cache-absent pool is byte-identical to the pre-M3 term.
    story_salient = _IfThenElse(
        _Eq(_Attr(_V(var), "coref_story_salience_on"), _Lit(1.0)),
        _Times([_Lit(_STORY_SALIENCE_W), _Attr(_V(var), "coref_story_salience")]),
        _Lit(0.0))
    # CONTENT-OVER-PRONOUN — a function-word (pronoun-surface) candidate is
    # dispreferred so a real named referent (the ass) beats a throwaway 'he' node
    # it out-recencies. 0.0 for every content candidate (missing OR 0.0 -> 0.0, the
    # is_prominent/story_salient IfThenElse idiom), so a pool with no pronoun-surface
    # entity — the crow — is byte-identical.
    fn_word_penalty = _IfThenElse(
        _Eq(_Attr(_V(var), "coref_function_word"), _Lit(1.0)),
        _Lit(-_FUNCTION_WORD_PENALTY), _Lit(0.0))
    return _Plus([
        is_prominent,
        _Times([_Lit(_CLEAN_BONUS), _Attr(_V(var), "coref_cleanliness")]),
        fn_word_penalty,
        _Times([_Lit(_CB_BONUS), is_cb]),
        story_salient,
        _Times([_Lit(_RECENCY_W), _Attr(_V(var), "coref_recency")]),
        _Neg(_Attr(_V(var), "coref_rolerank")),
    ])


def candidate_term(spec: dict, unit=None, exclude_name: Optional[str] = None) -> dict:
    """The licensed + agreeing candidate set: Filter(SmEntity pool, agreement).
    UNIT-SCOPED (MOVE 2b): when `unit` is given the pool is confined to entities
    carrying that `unit` attr, so a pronoun in episode 2 can only bind to episode
    2's entities (order-N isolation). `unit=None` is the flat, pre-2b pool.

    DISJOINT REFERENCE (Binding Principle B): `exclude_name`, when given, drops that
    entity from the pool. A NON-reflexive object pronoun ('the sparrow asked HIM')
    cannot co-refer with the SUBJECT of its own clause ('sparrow'); passing the
    subject's name here enforces that structural constraint as a filter conjunct,
    so 'him' can never bind back onto 'sparrow' (which is what dequantised the
    sparrow male). `None` = the flat pre-Principle-B pool (byte-identical)."""
    agree = _agreement_term("e", spec)
    conds = [agree]
    if unit is not None:
        conds.append(_Eq(_Attr(_V("e"), "unit"), _Lit(unit)))
    if exclude_name is not None:
        conds.append(_Not(_Eq(_Attr(_V("e"), "name"), _Lit(exclude_name))))
    agree = conds[0] if len(conds) == 1 else _And(conds)
    return _Filter(_entity_set(), "e", agree)


def antecedent_argmax_term(spec: dict, cb_name: Optional[str], unit=None,
                           exclude_name: Optional[str] = None) -> dict:
    """THE DECISION — an Argmax Program over the resident SmEntity pool, ranked
    by Centering (Cb bonus) + salience (recency, then role-rank). Evaluated
    natively; Python never picks the winner (mirrors native_vote.predict_vote_term
    / spatial_routing.passable_hop_term's Argmax-of-score shape). `exclude_name`
    threads Binding Principle B (disjoint reference) into the candidate set."""
    return _Argmax(candidate_term(spec, unit, exclude_name), "e", _score_term("e", cb_name))


# --------------------------------------------------------------------------- #
#  feature grounding — category/number, ONCE, at first mention.
# --------------------------------------------------------------------------- #
def _looks_proper(sentence: str, name: str) -> bool:
    """Is `name` spelled CAPITALIZED anywhere in the original (pre-lowercase)
    sentence? A thin I/O-boundary orthographic read (no NER model, no Rust
    primitive for it) — converts an opaque surface feature (capitalization)
    into the smallest graph token (proper-noun-ness), CLAUDE.md's permitted
    carve-out. No `import re`: plain str.split() + strip()."""
    for tok in sentence.split():
        t = tok.strip(".,!?;:\"'()")
        if t and t[0].isupper() and t.lower() == name:
            return True
    return False


# --------------------------------------------------------------------------- #
#  PROPER-NAME SPAN COMPLETION (Phase 3, 2026-07-13). Some upstream clause
#  reductions (e.g. a comma-appositive's shared-subject carry in
#  reading_collapse.decompose_sentence, or a rare head-token/verb collision
#  like the surname 'Levy' also being a common verb) keep only the FIRST
#  token of a multi-token proper name as a clause's subject span, so the
#  entity that reaches coref is named 'robert' instead of 'robert_levy'. THE
#  DECISION this closes: a proper name spanning multiple ADJACENT capitalised
#  tokens ('Robert Levy') is ONE entity, keyed by its FULL span, never just
#  its head token — held as a graph POLICY flag
#  (CorefNamingPolicy.keep_full_proper_span), not a Python literal `if`, so
#  ablating the flag (setting it 0.0) reverts to the truncated head, proving
#  the decision is the held datum, not the code around it.
# --------------------------------------------------------------------------- #
def _naming_policy_node(agent, *, create: bool = True):
    sub, native = _resolve(agent)
    for n in sub.nodes("CorefNamingPolicy"):
        return n
    if not create:
        return None
    return sub.add_node("CorefNamingPolicy", {"keep_full_proper_span": 1.0})


def _keep_full_proper_span(agent) -> bool:
    """The held POLICY: does the reader keep a multi-token proper name's full
    capitalised span as its entity's canonical name? Defaults ON (1.0) the
    first time the singleton mints. A graph-resident Attr read, mirroring the
    `coref_metrical_prominence`/`coref_story_salience_on` IfThenElse-gated
    FACTORS this module already threads through the Argmax score — here the
    gate sits in front of a mechanical I/O helper instead of a score term,
    because span-completion is a naming CORRECTION, not a candidate-ranking
    FACTOR, but the ablation discipline is the same: flip the held attr,
    watch the behaviour revert."""
    sub, _ = _resolve(agent)
    nid = _naming_policy_node(agent)
    return float(sub.node(nid)["attrs"].get("keep_full_proper_span", 1.0) or 0.0) != 0.0


def _proper_name_span(agent, sentence: str, name: str) -> str:
    """The FULL multi-token PROPER-NAME span `name` heads in `sentence`, or
    `name` unchanged when there is nothing to extend to (or the held policy
    is off — see `_keep_full_proper_span`).

    A thin orthographic I/O-boundary read off the ORIGINAL sentence — the
    SAME capitalisation scan `_looks_proper` (this module, just above)
    already performs: converts an opaque surface fact (adjacent
    capitalisation) into the smallest graph token (the entity's full span).
    No meaning decision, no NER model, no Rust primitive for it — the same
    carve-out `_looks_proper` already exercises. Scoped tight against a false
    extension:

      * `name` must be a SINGLE token that is itself capitalised in
        `sentence` (`_looks_proper`) — a name already carrying an underscore
        is already whole and is left untouched (idempotent on a second
        touch, e.g. an already-resolved pronoun's concept), and never a
        pronoun/deictic form itself (`_PRONOUNS`/`_DEIXIS`, already held
        data this module imports);
      * the ANCHOR occurrence itself must carry NO leading/trailing
        punctuation ('Sultan;', 'Hansel,', a quote-flanked '"Cease,') — a
        punctuated anchor is a DIALOGUE-TAG / vocative boundary, not the
        start of a name, so it never extends (audited live against the
        whole Aesop+Grimm corpus via this function's own ablation toggle —
        see the phase's commit/report for the full diff);
      * a continuation token extends the span only while it is ITSELF
        capitalised, is NOT ALL-CAPS (an emphasis run like 'WHY SHOULD' is
        not a name), and is NOT a held AUXILIARY/MODAL
        (`reading_collapse._AUX` — graph-backed closed-class data, the SAME
        set the clause reader already consults) or a pronoun/deixis form —
        this is what keeps a quote/verse-initial capitalised function word
        ('Will' in the fish-tale's "My wife Ilsabill / Will have her own
        will", 'I' opening the next quoted line) from being swept into the
        preceding name;
      * the run STOPS at the first token that carries its own
        leading/trailing punctuation ('Levy,' in 'Robert Levy, an
        attorney...' still joins the span — its comma is stripped before
        the capital-letter test — but ends the run there, so the
        appositive 'an attorney...' is never swept in);
      * a lone capitalised word ('Levy' by itself, 'The crow') returns
        `name` unchanged — nothing to extend to."""
    if not _keep_full_proper_span(agent):
        return name
    if not isinstance(name, str) or not name or "_" in name:
        return name
    if name in _PRONOUNS or name in _DEIXIS:
        return name
    if not _looks_proper(sentence, name):
        return name
    toks = sentence.split()
    n = len(toks)
    punct = ".,!?;:\"'()"
    for i, raw in enumerate(toks):
        clean = raw.strip(punct)
        if not (clean and clean[0].isupper() and clean.lower() == name):
            continue
        if raw != clean:
            return name        # punctuation-flanked anchor — a dialogue-tag boundary
        span = [clean]
        j = i + 1
        while j < n:
            nraw = toks[j]
            nclean = nraw.strip(punct)
            if not nclean or not nclean[0].isupper():
                break
            if len(nclean) > 1 and nclean.isupper():
                break           # ALL-CAPS emphasis run, not a name continuation
            nlow = nclean.lower()
            if nlow in _PRONOUNS or nlow in _DEIXIS or nlow in rc._AUX:
                break           # a pronoun/auxiliary/modal, not a name continuation
            span.append(nclean)
            if nraw != nclean:
                break                     # this token carried punctuation — run ends here
            j += 1
        return "_".join(t.lower() for t in span) if len(span) > 1 else name
    return name


def _grounded_category(sentence: str, name: str) -> str:
    """person / animal / object / unknown. A PROPER-NOUN surface is left
    "unknown": WordNet's top sense for 'john'/'bill' is a common NOUN (toilet /
    legislative bill), not the person named, so trusting it would be actively
    WRONG. "unknown" agrees permissively with a person-pronoun (never blocks a
    correct bind) and never satisfies a confident 'it' bind — the SAME honest
    stance reference_resolution.py takes on ungrounded gender."""
    if _looks_proper(sentence, name):
        return "unknown"
    from domains import dictionary_lexicon as dl
    try:
        r = dl.dictionary_lookup(name, "patient", "en")
    except Exception:
        r = None
    cat = (r or {}).get("category")
    return cat if cat in ("person", "animal", "object") else "unknown"


def _agent_grounded_category(sentence: str, name: str) -> str:
    """person / animal / object / unknown, grounded with the AGENT slot (expected
    {person, animal}) instead of _grounded_category's `patient` (expected {object,
    animal, person}). The patient slot gives NO animate/inanimate discrimination,
    so an entity like 'ass'/'cock'/'donkey' — whose WordNet frequency sense-1 is a
    NON-animal sense (buttocks / stopcock / donkeywork) — grounds `object`. The
    agent slot's expected {person, animal} makes the graph SELECTION rule's
    category-fit signal DISCRIMINATE the animate sense (cock -> cock.n.04 animal,
    donkey -> domestic_ass animal). A proper-noun surface is still left `unknown`
    (WordNet's sense of 'John' is a common noun). Mechanical adapter I/O — the
    SAME WordNet read _grounded_category does, only the slot query differs (the
    dictionary user flips to the animate section)."""
    if _looks_proper(sentence, name):
        return "unknown"
    from domains import dictionary_lexicon as dl
    try:
        r = dl.dictionary_lookup(name, "agent", "en")
    except Exception:
        r = None
    cat = (r or {}).get("category")
    return cat if cat in ("person", "animal", "object") else "unknown"


def _is_nonnominal_modifier(name: str) -> bool:
    """A one-token surface WordNet knows ONLY as an ADJECTIVE / ADVERB and NOT as a
    noun ('asleep', 'still', 'bright') — a predicate modifier the parser can nounify
    into a spurious entity ("they soon fell asleep" -> an `asleep` SmEntity). It is
    NOT an animate referent, so a person/animate pronoun must not bind it. TIGHT: a
    real noun ('dog') has a noun synset -> False; an UNKNOWN proper name / coinage
    with NO WordNet entry at all ('Jabberwock') has neither -> False (never demoted).
    Only a word with an adj/adverb sense AND no noun sense is caught."""
    from domains import consumption_quality as cq
    if not isinstance(name, str) or len(cq._tokens(name)) != 1:
        return False
    try:
        from nltk.corpus import wordnet as wn
        surf = name.replace("_", " ")
        if wn.synsets(surf, pos=wn.NOUN):
            return False
        return bool(wn.synsets(surf, pos=wn.ADJ) or wn.synsets(surf, pos=wn.ADV)
                    or wn.synsets(surf, pos=wn.ADJ_SAT))
    except Exception:
        return False


def _has_whole_animal_sense(word: str) -> bool:
    """The reader's OWN dictionary knowledge: does `word` denote a WHOLE LIVING
    CREATURE anywhere in WordNet — across ALL its senses, not just the frequency
    sense-1? True iff `word` has a `noun.animal` synset descended from
    chordate.n.01 (a vertebrate: mammal / bird / fish / reptile / amphibian) OR
    invertebrate.n.01 (an insect / mollusc / ...) — i.e. an ACTUAL creature. This is
    what grounds the acting protagonists whose FREQUENCY sense-1 is a non-animal
    homonym: 'ass' carries ass.n.03 (a donkey), 'cock' carries cock.n.04 (a
    rooster), 'donkey' carries domestic_ass.n.01 — the reader KNOWS these are animals
    even though the coarse first sense is buttocks / penis / donkeywork.

    The chordate/invertebrate ancestry is the PRECISION signal, tighter than a bare
    animal.n.01 hyponymy, separating a real creature from BOTH:
      · a BODY-PART-of-an-animal homonym ('teeth'->tooth.n.03, 'lips'->lip.n.05,
        'hair'->hair.n.06, 'tail'->tail.n.01) — a `noun.animal` synset that is a
        PART, not an organism, and is not under chordate/invertebrate; and
      · a GENERIC animal COUNTER ('head'->head.n.02 "a single domestic animal",
        under domestic_animal.n.01 directly off animal.n.01 — an anatomical /
        counting homonym, NOT a species), which a bare animal.n.01 test wrongly
        admitted.
    This is NOT a hardcoded animal list — it is a WordNet lexname + hypernymy read,
    the SAME reference-I/O status as _grounded_category's WordNet lookup (donkey = 0,
    no LLM). The whole set of creatures — ass/cock/donkey/dog/cat/kid/seal/bat/crane/
    sparrow/mouse/wolf/ant/bee/grasshopper/frog/snail/horse — resolves True; every
    body-part / counter homonym resolves False, from the taxonomy alone."""
    try:
        from nltk.corpus import wordnet as wn
        roots = (wn.synset("chordate.n.01"), wn.synset("invertebrate.n.01"))
        for s in wn.synsets(word, pos=wn.NOUN):
            if s.lexname() != "noun.animal":
                continue
            ancestors: set = set()
            for path in s.hypernym_paths():
                ancestors.update(path)
            if any(r in ancestors for r in roots):
                return True
    except Exception:
        return False
    return False


# --------------------------------------------------------------------------- #
#  ANIMACY GATE — an entity naming a DATE / SUBSTANCE / INSTITUTION is not an
#  animate referent and must NOT carry natural gender (the gender-leak precision
#  fix: '1891' / 'radium' / 'university' should never be dequantised female by an
#  ambient 'she'). Decoded from the reader's OWN dictionary (WordNet lexname),
#  NOT a name table — the SAME reference-I/O status as _has_whole_animal_sense.
#  GUARDED: an animal word (whole-animal sense) is caught by the animate branch
#  BEFORE this, and a PROPER noun in its sentence keeps the honest proper stance
#  (a capitalised 'Maria'/'Pierre'/'Crow'/'Birds' is NEVER demoted — the crow
#  fable's byte-identity guard, and what keeps a person's proper name animate).
# --------------------------------------------------------------------------- #
_INANIMATE_LEXNAMES = frozenset((
    "noun.substance", "noun.location", "noun.group", "noun.artifact",
    "noun.food", "noun.plant", "noun.object", "noun.shape", "noun.time",
    "noun.quantity", "noun.possession", "noun.phenomenon", "noun.body"))


def _is_inanimate_thing(name: str, sentence: str) -> bool:
    """Does `name` denote a NON-animate thing — a date/number, or a common noun the
    reader's dictionary knows ONLY as a concrete inanimate (a substance/place/
    institution/artifact), with NO person/animal sense? Such an entity cannot be a
    gendered animate referent. A DIGIT string ('1891') is a date/year. A PROPER noun
    in its sentence is left animate (the honest proper stance — a capitalised name may
    be a person). Otherwise WordNet decides: a whole-animal or person sense keeps it
    animate; only a purely concrete-inanimate common noun ('radium'->substance,
    'university'->group/artifact, 'legion'->group) is demoted. donkey=0, no import re."""
    if not isinstance(name, str) or not name:
        return False
    if name.isdigit():
        return True                          # a date / year / bare number
    if _looks_proper(sentence, name):
        return False                         # honest proper stance (may be a person)
    if _has_whole_animal_sense(name):
        return False
    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(name.replace("_", " "), pos=wn.NOUN)
    except Exception:
        return False
    if not syns:
        return False                         # unknown coinage -> not demoted (stays as-is)
    lexes = set()
    for s in syns:
        try:
            lexes.add(s.lexname())
        except Exception:
            continue
    if "noun.person" in lexes or "noun.animal" in lexes:
        return False                         # a person/animal sense -> keep animate
    return bool(lexes & _INANIMATE_LEXNAMES)


def _character_clean(name: str) -> bool:
    """Clean enough to be tracked as a CHARACTER: not a >=3-token parse-glom, AND
    (a nominal per the held faculty OR a WordNet whole-animal word). The whole-animal
    disjunct rescues a real animal word whose is_nominal is spuriously False from a
    slang FUNCTION reading — Wiktionary tags 'ass' a 'particle' (the big-ass
    intensifier), so _grounded_cleanliness (which is is_nominal) drops it, yet
    WordNet knowing 'ass' as a donkey (ass.n.03) is itself the proof it is a
    nominal. Same >=3-token glom guard as _grounded_cleanliness; this is a SEPARATE
    read (_grounded_cleanliness is left untouched, so the byte-identity coref
    scoring path is unchanged)."""
    from domains import consumption_quality as cq
    if not isinstance(name, str) or len(cq._tokens(name)) >= 3:
        return False
    if _has_whole_animal_sense(name):
        return True
    return cq.is_nominal(name.replace("_", " "))


def _animal_context(sub, unit=None) -> bool:
    """Is the read in an ANIMAL-CONTEXT — are the coherent co-characters animals?
    A pure situation-model read: >= 2 CLEAN tracked entities are ALREADY grounded
    `animal` (at first mention, before this pass — the sense-1 animals
    dog/cat/wolf/...), so the story is an animal tale and an un-discriminated entity
    naming an animal ('cock' -> rooster) coheres as one of its characters even when
    that word never itself becomes an eventive agent. The crow fable produces ZERO
    sense-1 animals (its 'Crow'/'Birds' are PROPER -> `unknown`), so it is NOT an
    animal-context and the context branch never fires there (byte-identity guard)."""
    n = 0
    for node in sub.nodes("SmEntity"):
        at = sub.node(node)["attrs"]
        if unit is not None and at.get("unit") != unit:
            continue
        nm = at.get("name")
        if isinstance(nm, str) and at.get("coref_category") == "animal" \
                and _character_clean(nm):
            n += 1
            if n >= 2:
                return True
    return False


def _refine_animacy_from_agency(agent, textbase: list, *, unit=None) -> list:
    """AGENCY (or an ANIMAL-CONTEXT) IMPLIES ANIMACY — a post-read categorization
    refinement pass. Grounds an entity as an ANIMAL from the reader's OWN knowledge.

    A tracked story entity is a CHARACTER — a person or animal, never an inanimate
    object — when the word naming it denotes a whole animal AND it either ACTS in the
    narrative OR the coherent co-characters are animals. The first-mention grounding
    (_grounded_category) runs with the `patient` slot, whose expected {object,
    animal, person} gives NO animate discrimination, so it falls to WordNet's
    FREQUENCY sense-1 — which for a class of real-prose animal names ('ass' ->
    buttocks, 'cock' -> penis/stopcock, 'donkey' -> donkeywork) is a NON-animal
    homonym, leaving those animal characters mis-categorised `object`. (Most animal
    names — dog/cat/wolf/boar/mouse/sparrow/frog/bird/goat/lion/fox — already ground
    animal at sense-1 and need no help; this pass is for the sense-1-non-animal
    minority.) The pass OVERWRITES coref_category to `animal` only when ALL of:

      (a) the current category is the un-discriminated `object`/`unknown` (the
          PRECISION LOCK — an already-clean-sensed animal/person/object category is
          never overridden);
      (b) the word has a WordNet `noun.animal` sense ANYWHERE (across all senses)
          that is a WHOLE LIVING ANIMAL — a hyponym of animal.n.01
          (_has_whole_animal_sense). This is the reader's OWN dictionary knowledge,
          not a hardcoded list. The animal.n.01 hyponymy is the BODY-PART precision:
          'teeth'/'lips'/'hair'/'tail' carry a `noun.animal` synset but it is a
          PART, not an organism, so they are rejected;
      (c) it ACTS — is the AGENT (arg0) of an EVENTIVE verb (WordNet's own verb
          classification, situation_model_reader.eventive_membership) — OR it is in
          an ANIMAL-CONTEXT (>= 2 clean co-characters are already animals). Agency
          promotes the acting leads ('ass', 'donkey'); the animal-context promotes a
          coherent animal character that is only ever a grammatical OBJECT in the
          prose ('cock', met but not itself acting) WITHOUT admitting a body-part
          homonym (rejected by (b)) or a non-animal in a non-animal text (no context);
      (d) it is NOT a >=3-token parse-glom ('ran_across_his_paws' is not a
          character);
      (e) it is NOT a proper noun in its first sentence (the honest proper stance is
          kept — a capitalised 'Crow'/'Birds' stays `unknown`; this is the crow
          fable's byte-identity guard).

    A short clean fable NEVER triggers a write — its object/unknown entities have no
    whole-animal sense (water/cheese) and it is not an animal-context, so the pass
    returns an EMPTY rewrite list (zero graph mutations) on every short dev fable +
    the crow: BYTE-IDENTICAL. Mechanical adapter I/O — WordNet reads + an attr write,
    the SAME status as _grounded_category. WordNet + the situation model decide the
    category; no `if`/`else` picks a MEANING over graph state, no Python winner-pick.
    Returns the list of {name, from, to} rewrites (for the caller/tests to inspect)."""
    from domains import situation_model_reader as smr
    from domains import consumption_quality as cq
    sub, native = _resolve(agent)
    # first sentence each surface appears in (any slot) + the set of surfaces that
    # are the AGENT (arg0) of an EVENTIVE verb (WordNet's own verb classification,
    # smr.eventive_membership). Both mechanical scans of the already-committed
    # textbase (no re-parse).
    first_sentence: dict = {}
    eventive_agents: set = set()
    for tb in textbase:
        sent = tb.get("sentence", "") or ""
        for pred in tb.get("predications") or []:
            if not pred or len(pred) < 2:
                continue
            for arg in [str(a) for a in pred[1:]]:
                first_sentence.setdefault(arg, sent)
            rel, subj = str(pred[0]), str(pred[1])
            if smr._is_property_pred(rel.lower()):
                continue
            if smr.eventive_membership(agent, rel)["eventive"]:
                eventive_agents.add(subj)
    animal_ctx = _animal_context(sub, unit)               # situation-model read (co-characters)
    rewrites = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if not isinstance(nm, str) or not nm:             # numeral / non-string name: not a character
            continue
        if unit is not None and at.get("unit") != unit:
            continue
        cur = at.get("coref_category")
        if cur not in ("object", "unknown"):              # (a) precision lock
            continue
        if len(cq._tokens(nm)) >= 3:                      # (d) not a parse-glom
            continue
        if _looks_proper(first_sentence.get(nm, ""), nm):  # (e) proper stance — protects capitalised Crow/Birds
            continue
        if not _has_whole_animal_sense(nm):               # (b) the reader's own WordNet animal knowledge
            continue
        if not (nm in eventive_agents or animal_ctx):      # (c) acts OR animal-context
            continue
        sub.set_attr(n, "coref_category", "animal")
        rewrites.append({"name": nm, "from": cur, "to": "animal"})
    return rewrites


def _grounded_cleanliness(name: str) -> float:
    """1.0 (clean, groundable nominal) or 0.0 (junk blob). A candidate
    SmEntity's NAME is CLEAN iff it is not a long multi-word underscore glom
    AND it grounds as a nominal per the held nominal faculty
    (consumption_quality.is_nominal, the SAME leaf reading_collapse._is_real_
    nominal / the enum path's nominal_filter use):

      * >=3 underscore-joined tokens is the SHAPE an imperfectly-parsed
        clause fragment takes (a whole subject+verb span glommed into one
        name, e.g. 'poor_thing_felt' -- 'the poor thing felt', 'no_matter_
        how_he_tried_...') -- is_nominal alone does not catch this (each
        WORD in the blob still has some noun reading, e.g. 'felt' the
        fabric), so token-count is the honest additional structural signal;
      * a 1-2 token name (a bare word, or a short compound like
        'narrow_neck') is judged by is_nominal on its de-underscored surface
        -- the SAME faculty used everywhere else in this codebase to tell a
        noun phrase from a clause/verb-phrase fragment.

    A property of the REFERENT's name, grounded ONCE at first mention (the
    same convention as coref_category/coref_number)."""
    from domains import consumption_quality as cq
    toks = cq._tokens(name)
    if len(toks) >= 3:
        return 0.0
    return 1.0 if cq.is_nominal(name.replace("_", " ")) else 0.0


def _is_function_word_name(name: str) -> bool:
    """Is `name`'s head a CLOSED-CLASS function word (a pronoun/determiner)? Read
    off the held closed-class faculty (function_word_reference.classify — the SAME
    lexicon narrative_structure._is_function_word / consumption_quality._function_of
    consult), a mechanical lexical lookup. A content noun (crow/ass/dog/robbers) is
    False. Used to disprefer a throwaway pronoun-surface antecedent ('he') over a
    real named referent.

    A WHOLE-ANIMAL word is RESCUED (never a function word): Wiktionary tags 'ass'
    a 'particle' (the big-ass intensifier), which would wrongly penalise the ass
    as a pronoun-surface — the SAME slang-function mis-read _character_clean
    already rescues via the whole-animal sense (WordNet knowing 'ass' as a donkey
    is itself the proof it is a content noun, not a function word)."""
    if _has_whole_animal_sense(name):
        return False
    from domains import function_word_reference as fw
    head = str(name).split("_")[-1]
    try:
        return bool((fw.classify(head, "en") or {}).get("function"))
    except Exception:
        return False


def _grounded_number(name: str) -> str:
    """plural iff the held WordNet morphy lemmatiser maps this surface to a
    DIFFERENT singular lemma ('boys'->'boy', 'children'->'child') — the SAME
    nltk morphy signal situation_model_reader._lemma already uses for verbs,
    applied to nouns. COARSE + documented: an irregular plural morphy does not
    lemmatise ('men') reads as singular (matching reference_resolution.py's own
    coarse-number honesty)."""
    try:
        from nltk.corpus import wordnet as wn
        lemma = wn.morphy(name, "n")
        if lemma and lemma != name:
            return "plural"
    except Exception:
        pass
    return "singular"


def _touch_entity(agent, sentence: str, name: str, role: str, turn: int, *, unit=None):
    """Ensure `name`'s SmEntity carries coref bookkeeping and update its
    recency/role/mentions for this turn. Category/number are grounded ONCE, at
    first mention (properties of the referent, not of any one mention) —
    mechanical adapter state, the same status as situation_model_reader's own
    `mentions`/`recency` attrs."""
    sub, native = _resolve(agent)
    nid = smr._entity(agent, name, unit=unit)           # mint-or-fetch, REUSED as-is
    at = sub.node(nid)["attrs"]
    if "coref_category" not in at:
        cat = _grounded_category(sentence, name)
        sub.set_attr(nid, "coref_category", cat)
        sub.set_attr(nid, "coref_number", _grounded_number(name))
        sub.set_attr(nid, "coref_cleanliness", _grounded_cleanliness(name))
        sub.set_attr(nid, "coref_mentions", 0.0)
        sub.set_attr(nid, "coref_metrical_prominence", 0.0)   # 0.0 until verse-licensed
        # GENDER SHAPE — decoded per entity, ONCE at first mention (a property of
        # the referent, like category/number). `coref_animate` is the shape's
        # animacy feature: an animate character (person/animal/unknown, OR a word
        # WordNet knows as a whole animal — the ass's ass.n.03) can take a
        # gendered pronoun. `coref_gender` is the decoded natural-gender PRIOR
        # (word-dequant + object-properties); "" = UNDERSPECIFIED, established
        # dynamically by the first gendered pronoun (the context dequant in
        # resolve_pronoun). Decoded from evidence, never a per-referent table.
        # ANIMACY (extended): an `unknown`-category entity is animate ONLY when it
        # is a genuine CHARACTER-clean nominal (a proper name / common noun the
        # coref pool already tracks as a character). A NON-nominal `unknown` glom —
        # an adjective/state the parser nounified into a spurious entity
        # ('asleep' from "they soon fell asleep") — is NOT an animate referent, so
        # a person/animate pronoun ('he'/'him') never grabs it as an antecedent.
        # person/animal (and whole-animal words) stay animate exactly as before;
        # only the junk-`unknown` case is demoted (targeted, byte-id elsewhere).
        if cat in ("person", "animal") or _has_whole_animal_sense(name):
            animate = 1.0
        elif _is_nonnominal_modifier(name):
            animate = 0.0                       # an adjective/adverb glom ('asleep')
        elif _is_inanimate_thing(name, sentence):
            animate = 0.0                       # a date/substance/institution — NEVER gendered
        else:
            animate = 1.0 if cat == "unknown" else 0.0
        sub.set_attr(nid, "coref_animate", animate)
        g0 = gs.decode_gender(name, sentence, "en")
        sub.set_attr(nid, "coref_gender", g0)
        # PROVENANCE: a decoded natural-gender prior ("king" -> male) is a STRONG
        # (definitional) belief -- it resists later revision. An underspecified
        # prior ("" ) mints no belief; the first gendered pronoun will (as a weak
        # reader-inference) in resolve_pronoun.
        if g0 in ("male", "female"):
            _belief_set(agent, name, "gender", g0,
                        source=_SOURCE_DEFINITIONAL,
                        confidence=_BELIEF_STRONG_CONF, turn=turn)
        sub.set_attr(nid, "coref_function_word", 1.0 if _is_function_word_name(name) else 0.0)
        at = sub.node(nid)["attrs"]
    sub.set_attr(nid, "coref_recency", float(turn))
    sub.set_attr(nid, "coref_rolerank", float(_ROLE_RANK.get(role, _DEFAULT_ROLE_RANK)))
    sub.set_attr(nid, "coref_mentions", float(at.get("coref_mentions", 0.0) or 0.0) + 1.0)
    return nid


# --------------------------------------------------------------------------- #
#  Cf / Cb bookkeeping — discourse-history STATE (what was said), not the
#  antecedent DECISION (which entity a pronoun binds to, above). One singleton
#  CorefCentering node per agent.
# --------------------------------------------------------------------------- #
def _centering_node(agent):
    sub, native = _resolve(agent)
    for n in sub.nodes("CorefCentering"):
        return n
    return sub.add_node("CorefCentering", {"cb": "", "cf": "[]", "turn": 0.0})


def _current_cb(agent) -> Optional[str]:
    sub, native = _resolve(agent)
    at = sub.node(_centering_node(agent))["attrs"]
    cb = at.get("cb") or ""
    return cb or None


def _update_centering(agent, realized: dict, turn: int) -> dict:
    """Cf = this turn's realized entities ranked by role; Cb = the highest-
    ranked entity of the PREVIOUS turn's Cf realized again now (Grosz-Joshi-
    Weinstein, reusing reference_resolution.py's exact update rule). Recording
    turn history, not choosing an antecedent."""
    sub, native = _resolve(agent)
    nid = _centering_node(agent)
    at = sub.node(nid)["attrs"]
    prev_cf = json.loads(at.get("cf") or "[]")
    cf = sorted(realized.keys(),
                key=lambda c: _ROLE_RANK.get(realized[c], _DEFAULT_ROLE_RANK))
    cb = next((c for c in prev_cf if c in realized), None)
    sub.set_attr(nid, "cb", cb or "")
    sub.set_attr(nid, "cf", json.dumps(cf))
    sub.set_attr(nid, "turn", float(turn))
    return {"cf": cf, "cb": cb}


# --------------------------------------------------------------------------- #
#  DEICTIC CENTRE — WHO is speaking / addressed RIGHT NOW. First/second person
#  are DEIXIS: they point at the discourse centre, not a salient antecedent. One
#  singleton DeicticCentre node per agent, holding the CURRENT speaker/addressee
#  as a REVISABLE cache: carried forward across sentences, RE-COLLAPSED whenever a
#  speech-act tag names a new speaker (so 'cried he' AFTER the quote still binds
#  the quote's 'I'). The speaker is the AGENT of a communication act — WordNet's
#  verb.communication classification, not a hand-listed verb set. Absent until the
#  first speech act (a text with no direct speech never mints this node — the crow
#  fable path is byte-identical: no DeicticCentre, no deixis forms present).
# --------------------------------------------------------------------------- #
def _deictic_node(agent, *, create: bool = True):
    sub, native = _resolve(agent)
    for n in sub.nodes("DeicticCentre"):
        return n
    if not create:
        return None
    return sub.add_node("DeicticCentre", {"speaker": "", "addressee": "", "turn": 0.0})


def _deictic_role(agent, role: str) -> Optional[str]:
    """The current `speaker` / `addressee` name held in the deictic centre, or None
    when unset (no speech act yet). A pure graph read."""
    sub, _ = _resolve(agent)
    nid = _deictic_node(agent, create=False)
    if nid is None:
        return None
    val = sub.node(nid)["attrs"].get(role) or ""
    return val or None


def _entity_by_name(agent, name: str):
    sub, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def _resolve_pron_name(agent, surface: str, unit=None) -> Optional[str]:
    """A third-person pronoun ('cried HE') resolved to a NAME through the held
    salience Argmax, read-only (no Mention minted). None when unresolved."""
    sub, native = _resolve(agent)
    pron_g = gs.pronoun_gender(surface)
    spec = dict(_PRONOUNS[surface])
    if pron_g:
        spec["gender"] = pron_g
    winner = native.evaluate(antecedent_argmax_term(spec, _current_cb(agent), unit), {})
    return sub.node(winner)["attrs"].get("name") if winner is not None else None


def _is_communication(pred: list) -> bool:
    return (pred and len(pred) >= 2
            and smr._verb_lexname(smr._lemma(str(pred[0]))) == "verb.communication")


def _is_speechlike(pred: list) -> bool:
    """A predication that ATTRIBUTES an utterance — a WordNet communication verb
    ('said'/'answered') OR a `designate` relation a speech verb mis-fired into
    (\"'...' said X\" often reads as designate because 'say/cry' are WordNet-near the
    naming anchor 'call'). Both carry the same quoted-subject inversion a direct
    quote induces, so both are candidates for the narrow drop below."""
    if not pred or len(pred) < 2:
        return False
    return (str(pred[0]).lower() == "designate" or _is_communication(pred))


def _arg_is_participant(agent, x: str) -> bool:
    """Is `x` a plausible DISCOURSE PARTICIPANT (a speaker/addressee) — a covered
    pronoun/deixis form, or a RESIDENT entity (an established referent, whatever its
    category — a proper-name character like 'sultan' is categorised 'unknown' yet is
    a real participant) — rather than fresh quoted content?"""
    xs = x.lower()
    if xs in _PRONOUNS or xs in _DEIXIS:
        return True
    return _entity_by_name(agent, x) is not None


def _quoted_subject_inversion(agent, pred: list, unit=None):
    """The NARROW speech-act inversion a direct quote induces: \"'quote' said the
    sparrow\" parses with the QUOTED CONTENT in the subject slot (arg0) and the real
    SPEAKER post-posed (arg1). Detect ONLY this case — arg0 is FRESH quoted content
    (NOT a covered pronoun and NOT an already-resident referent) while arg1 IS a
    discourse participant (a pronoun or a resident referent) — and return
    (speaker, message). Returns None for every normal speech act: a resident-subject
    tag ('sultan told the wolf' — sultan is resident, so arg0 is a participant) and a
    pronoun-subject tag are BOTH left UNTOUCHED.     This tightness (residence, not
    animacy) is what stops the rule from dropping a proper-name speaker; only a
    never-seen quoted epithet ('wretch') in the subject slot is removed."""
    if not _is_speechlike(pred) or len(pred) < 3:
        return None
    a0, a1 = str(pred[1]), str(pred[2])
    if _arg_is_participant(agent, a0):
        return None                                # arg0 is a resident/pronoun speaker -> normal
    if not _arg_is_participant(agent, a1):
        return None                                # arg1 is not a participant -> not this case
    speaker = a1
    if speaker.lower() in _PRONOUNS:
        speaker = _resolve_pron_name(agent, speaker.lower(), unit) or speaker
    return speaker, a0                             # (speaker, quoted message)


def _speech_centre_speaker(agent, pred: list, unit=None) -> Optional[str]:
    """The SPEAKER of a speech act, for setting the deictic centre (non-destructive):
    the inverted-quote speaker (arg1) when `_quoted_subject_inversion` fires, else
    the ordinary subject arg0 when it is a discourse participant. None otherwise."""
    if not _is_communication(pred):
        return None
    inv = _quoted_subject_inversion(agent, pred, unit=unit)
    if inv is not None:
        return inv[0]
    a0 = str(pred[1])
    if _arg_is_participant(agent, a0):
        return _resolve_pron_name(agent, a0.lower(), unit) or a0 if a0.lower() in _PRONOUNS else a0
    return None


def _update_deictic_centre(agent, preds: list, turn: int, unit=None) -> Optional[str]:
    """RE-COLLAPSE the deictic centre from this sentence's speech-act tag, BEFORE
    any of the sentence's predications are resolved — so a first-person form in a
    QUOTED span binds to the tag's speaker whether the tag precedes ('said the
    sparrow, ...') or FOLLOWS the quote (\"'...I am!' cried he\"). Reads the speaker
    off `_speech_centre_speaker` (inversion-aware). The previous speaker becomes the
    addressee (the adjacency-pair flip), kept in the cache. When the sentence carries
    NO speech tag the centre is left UNCHANGED (carried forward), so an implied-quote
    continuation keeps the established speaker. Mechanical adapter I/O."""
    speaker = None
    for p in preds:
        cand = _speech_centre_speaker(agent, p, unit=unit)
        if cand:
            speaker = cand
            break
    if speaker is None:
        return None                                # no tag — carry the cache forward
    sub, native = _resolve(agent)
    nid = _deictic_node(agent)
    prev = sub.node(nid)["attrs"].get("speaker") or ""
    if prev and prev != speaker:
        sub.set_attr(nid, "addressee", prev)       # the prior speaker is now addressed
    sub.set_attr(nid, "speaker", speaker)
    sub.set_attr(nid, "turn", float(turn))
    return speaker


def arm_deictic_centre(agent, *, speaker=None, addressee=None) -> dict:
    """MECHANICAL I/O: arm the deictic centre from an EXTERNAL, caller-supplied
    identity (the live Interlocutor/Agent turn) rather than an in-text speech-act
    tag -- so first/second person in a text with NO quoted dialogue (a chat turn,
    an imperative addressed to the reader) still binds 'I'/'you' to a REAL
    referent instead of minting an ungrounded SmEntity. `speaker`/`addressee` are
    each either a resident SmEntity node id or a plain name string (a string
    get-or-creates its SmEntity via `situation_model_reader._entity`, the same
    idiom every other entity mint in this module uses, so the bind below finds a
    real node). Passing None for a role leaves it UNCHANGED (partial re-arming is
    fine -- e.g. re-arming only the addressee on a turn flip). An in-text speech-
    act tag encountered AFTERWARDS still overrides/updates the centre via the
    UNCHANGED `_update_deictic_centre` path -- this is only the external arming
    SOURCE, not a new precedence rule. No decision here: a lookup-or-mint, then
    two attribute writes."""
    sub, native = _resolve(agent)

    def _name_of(x):
        if x is None:
            return None
        if isinstance(x, str):
            smr._entity(agent, x)              # get-or-create -> the bind below finds it
            return x
        node = sub.node(x)
        return (node["attrs"].get("name") if node else None) or None

    nid = _deictic_node(agent)
    sname = _name_of(speaker)
    aname = _name_of(addressee)
    if sname is not None:
        sub.set_attr(nid, "speaker", sname)
    if aname is not None:
        sub.set_attr(nid, "addressee", aname)
    return {"speaker": sub.node(nid)["attrs"].get("speaker") or None,
            "addressee": sub.node(nid)["attrs"].get("addressee") or None}


def _resolve_deixis(agent, surface: str, deixis: dict, sentence: str, turn: int) -> dict:
    """Bind ONE first/second-person occurrence to the deictic centre — DIRECT
    (deixis is not a salience contest): first person -> speaker, second -> addressee.
    Mints the Mention + `refers_to` edge to the resident centre entity if it exists
    (so the mention count lands on the real speaker, not a spawned 'i'); if the
    centre role is unset the mention is HELD OPEN, never force-bound. Returns the
    resolution trace in the same shape resolve_pronoun returns."""
    sub, native = _resolve(agent)
    person = deixis.get("person")
    role = "speaker" if person == "first" else "addressee"
    mention = sub.add_node("SmMention", {"surface": surface, "sentence": sentence,
                                          "t": float(turn), "deixis": person})
    name = _deictic_role(agent, role)
    if not name:
        sub.set_attr(mention, "held_open", 1.0)
        sub.set_attr(mention, "reason", "no %s in the deictic centre yet" % role)
        return {"resolved": False, "surface": surface, "mention": smr._v(mention),
                "reason": "no %s established" % role}
    # bind the mention to the resident centre entity when it exists (mechanical edge
    # write, like resolve_pronoun) — the SUBSTITUTION below is what folds a self-
    # predication onto the speaker even before the entity is minted.
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == name:
            smr._edge(native, mention, "refers_to", n)
            sub.set_attr(mention, "held_open", 0.0)
            break
    return {"resolved": True, "surface": surface, "mention": smr._v(mention),
            "concept": name, "rule": "deixis:%s->%s" % (person, role)}


# --------------------------------------------------------------------------- #
#  REVISABLE FEATURE BELIEFS — a general (feature-agnostic) provenance layer.
#
#  A `FeatureBelief` node per (entity, feature) carries {value, source,
#  confidence, support, first/last_turn, conflict_count, anomaly} + edges
#  `about -> SmEntity` and `established_by -> Mention`. The CURRENT collapsed
#  value is MIRRORED to the entity's live attr (gender -> `coref_gender`) so the
#  Argmax hot path is byte-identical; the belief node holds the provenance the
#  surprise loop reads and revises. Gender is the first consumer, but nothing
#  here is gender-specific.
# --------------------------------------------------------------------------- #
def _belief_find(agent, entity_name: str, feature: str):
    sub, _ = _resolve(agent)
    for n in sub.nodes("FeatureBelief"):
        at = sub.node(n)["attrs"]
        if at.get("entity") == entity_name and at.get("feature") == feature:
            return n
    return None


def _belief_read(agent, entity_name: str, feature: str) -> Optional[dict]:
    nid = _belief_find(agent, entity_name, feature)
    if nid is None:
        return None
    sub, _ = _resolve(agent)
    at = dict(sub.node(nid)["attrs"])
    at["_node"] = nid
    return at


def _mirror_attr_for(feature: str) -> Optional[str]:
    """The live entity attr a feature's collapsed value mirrors to (the hot
    path the Argmax filter reads). Only gender has one today; other features
    carry their belief without a legacy mirror."""
    return "coref_gender" if feature == "gender" else None


def _belief_set(agent, entity_name: str, feature: str, value, *, source: str,
                confidence: float, turn: int, established_by=None):
    """Mint-or-update the (entity, feature) belief and MIRROR its value to the
    entity's live attr. Fresh mint => support 1; an update keeps whatever the
    caller records via _belief_bump/_belief_conflict."""
    sub, native = _resolve(agent)
    nid = _belief_find(agent, entity_name, feature)
    if nid is None:
        nid = sub.add_node("FeatureBelief", {
            "entity": entity_name, "feature": feature, "value": value,
            "source": source, "confidence": float(confidence), "support": 1.0,
            "conflict_count": 0.0, "anomaly": 0.0,
            "first_turn": float(turn), "last_turn": float(turn)})
        ent = _entity_by_name(agent, entity_name)
        if ent is not None:
            smr._edge(native, nid, "about", ent)
    else:
        sub.set_attr(nid, "value", value)
        sub.set_attr(nid, "source", source)
        sub.set_attr(nid, "confidence", float(confidence))
        sub.set_attr(nid, "last_turn", float(turn))
    if established_by is not None:
        smr._edge(native, nid, "established_by", established_by)
    mirror = _mirror_attr_for(feature)
    if mirror is not None:
        ent = _entity_by_name(agent, entity_name)
        if ent is not None:
            sub.set_attr(ent, mirror, value)
    return nid


def _belief_bump(agent, entity_name: str, feature: str, turn: int):
    """A later observation CONSISTENT with the held value: +1 support."""
    nid = _belief_find(agent, entity_name, feature)
    if nid is None:
        return
    sub, _ = _resolve(agent)
    at = sub.node(nid)["attrs"]
    sub.set_attr(nid, "support", float(at.get("support", 0.0) or 0.0) + 1.0)
    sub.set_attr(nid, "last_turn", float(turn))


def _belief_conflict_bump(agent, entity_name: str, feature: str) -> float:
    """A CONFLICTING observation (a surprise): +1 conflict_count; return the
    running count so the collapse can weigh accumulated surprise."""
    nid = _belief_find(agent, entity_name, feature)
    if nid is None:
        return 0.0
    sub, _ = _resolve(agent)
    cc = float(sub.node(nid)["attrs"].get("conflict_count", 0.0) or 0.0) + 1.0
    sub.set_attr(nid, "conflict_count", cc)
    return cc


# --------------------------------------------------------------------------- #
#  THE EXPLANATION COLLAPSE — a native Argmax over {keep, reader_wrong,
#  writer_wrong, character_wrong, referent_changed}. The DECISION is the graph's
#  (a MaxOver picks the winning `Explanation` node by its score Term); Python
#  reads back the winning `kind` and performs the mechanical write for it. No
#  Python if/else CHOOSES the explanation.
# --------------------------------------------------------------------------- #
def _ensure_explanations(agent):
    sub, _ = _resolve(agent)
    have = {sub.node(n)["attrs"].get("kind") for n in sub.nodes("Explanation")}
    for k in _EXPLANATIONS:
        if k not in have:
            sub.add_node("Explanation", {"kind": k})


def _explanation_score_term() -> dict:
    """Score each `Explanation` node from the held belief's provenance (passed
    via env as scalars) and the accumulated conflicting evidence. `keep` is the
    null: it grows with the belief's confidence + support, so a strong or
    well-supported belief is never overturned. `reader_wrong` beats `keep` only
    when the belief is a WEAK reader-inference AND the surprise has piled up."""
    def isk(k):
        return _IfThenElse(_Eq(_Attr(_V("x"), "kind"), _Lit(k)), _Lit(1.0), _Lit(0.0))
    keep = _Plus([
        _Lit(_KEEP_BASE),
        _Times([_Lit(_KEEP_CONF_W), _V("b_conf")]),
        _Times([_Lit(_KEEP_SUPPORT_W), _V("b_support")]),
    ])
    reader = _Plus([
        _Times([_Lit(_SURPRISE_EV_W), _V("ev")]),
        _Neg(_Times([_Lit(_REVISE_CONF_W), _V("b_conf")])),
        _Neg(_Times([_Lit(_REVISE_SUPPORT_W), _V("b_support")])),
    ])
    # writer/character wrong: only representable when the belief was ASSERTED by
    # a writer/character (not a reader inference); an isolated conflict then
    # flags an anomaly rather than revising. Scored just above `keep` so it wins
    # ONLY over reader_wrong (never over a legitimately strong keep).
    assert_keep = _Plus([_V("ev"), _Neg(_V("b_support"))])
    return _Plus([
        _Times([isk("keep"), keep]),
        _Times([isk("reader_wrong"), _V("src_reader"), reader]),
        _Times([isk("writer_wrong"), _V("src_writer"), assert_keep]),
        _Times([isk("character_wrong"), _V("src_character"), assert_keep]),
        _Times([isk("referent_changed"), _V("changed_ev")]),
    ])


def _explain_surprise(agent, entity_name: str, feature: str, ev: float) -> str:
    """Run the explanation-collapse Argmax; return the winning explanation's
    `kind`. Provenance scalars are read mechanically from the belief and passed
    into the Term env; the Term (in Rust) picks the winner."""
    _ensure_explanations(agent)
    sub, native = _resolve(agent)
    belief = _belief_read(agent, entity_name, feature) or {}
    src = belief.get("source", "")
    env = {
        "b_conf": float(belief.get("confidence", 0.0) or 0.0),
        "b_support": float(belief.get("support", 0.0) or 0.0),
        "ev": float(ev),
        "src_reader": 1.0 if src == _SOURCE_READER else 0.0,
        "src_writer": 1.0 if src == _SOURCE_WRITER else 0.0,
        "src_character": 1.0 if src == _SOURCE_CHARACTER else 0.0,
        "changed_ev": 0.0,   # referent-split is a documented, un-armed sub-rung
    }
    winner = native.evaluate(
        _Argmax(_NodesOfType("Explanation"), "x", _explanation_score_term()), env)
    if winner is None:
        return "keep"
    return sub.node(winner)["attrs"].get("kind", "keep")


def _rebind_stray_mention(agent, mention, exclude_name: str, cb_name, unit) -> Optional[str]:
    """The Mention that established a now-revised belief was bound to the wrong
    entity. Re-run ITS OWN salience Argmax excluding that entity, redirect the
    `refers_to` edge to the next-best antecedent. Idempotent (a repeat call
    lands on the same winner and the edge set is unchanged)."""
    sub, native = _resolve(agent)
    surf = str(sub.node(mention)["attrs"].get("surface", "")).lower()
    spec = _PRONOUNS.get(surf)
    if spec is None:
        return None
    pron_g = gs.pronoun_gender(surf)
    spec = dict(spec)
    if pron_g:
        spec["gender"] = pron_g
    cand = _Filter(candidate_term(spec, unit), "e",
                   _Not(_Eq(_Attr(_V("e"), "name"), _Lit(exclude_name))))
    winner = native.evaluate(_Argmax(cand, "e", _score_term("e", cb_name)), {})
    if winner is None:
        return None
    new_name = sub.node(winner)["attrs"].get("name")
    for old in sub.neighbours(mention, "refers_to"):
        if sub.node(old)["attrs"].get("name") != new_name:
            sub.remove_edge(mention, "refers_to", old)
    smr._edge(native, mention, "refers_to", winner)
    return new_name


def _revise_reader_wrong(agent, entity_name: str, feature: str, new_value,
                         turn: int, cb_name, unit) -> dict:
    """reader_wrong verdict: the held (reader-inferred) belief was a mis-bind.
    Flip the belief value + mirror; retroactively rebind the stray establishing
    Mention to its next-best antecedent; record the revision on the belief node
    for introspection. The current pronoun is bound by the caller (the entity is
    now gender-consistent, so the normal filtered Argmax admits it)."""
    sub, native = _resolve(agent)
    bnid = _belief_find(agent, entity_name, feature)
    strays = list(sub.neighbours(bnid, "established_by")) if bnid is not None else []
    old_value = sub.node(bnid)["attrs"].get("value") if bnid is not None else None
    rebound = []
    for m in strays:
        nn = _rebind_stray_mention(agent, m, entity_name, cb_name, unit)
        if nn is not None:
            rebound.append(nn)
    _belief_set(agent, entity_name, feature, new_value, source=_SOURCE_READER,
                confidence=float(_SURPRISE_EV_W), turn=turn)
    if bnid is not None:
        sub.set_attr(bnid, "support", 1.0)
        sub.set_attr(bnid, "conflict_count", 0.0)
        sub.set_attr(bnid, "revised_at_turn", float(turn))
        sub.set_attr(bnid, "revised_from", old_value if old_value is not None else "")
        # the establishing mentions have been re-pointed; drop them as evidence
        for m in strays:
            sub.remove_edge(bnid, "established_by", m)
    return {"revised": True, "feature": feature, "entity": entity_name,
            "from": old_value, "to": new_value, "rebound_to": rebound}


# --------------------------------------------------------------------------- #
#  BRIDGING ANAPHORA / SET-MEMBERSHIP — a singular pronoun ('he'/'him') whose
#  referent is an INDIVIDUAL of a salient PLURAL group ('one of them' -> the
#  returning robber). The number-aware agreement filter (correctly) refuses to
#  bind a singular pronoun to a plural entity; when that plural GROUP is
#  nonetheless the most-salient antecedent (it outscores every surviving
#  singular), the pronoun denotes a MEMBER of it. We INDIVIDUATE that member
#  (a singular SmEntity `member_of` the group) so the agent's own salience
#  Argmax binds the pronoun to it and events form with the member as
#  participant. A WEAK, REVISABLE inference (a FeatureBelief records it) — a
#  later conflicting observation escalates through the same surprise/collapse
#  loop the gender belief rides.
# --------------------------------------------------------------------------- #
def _singularize(name: str) -> str:
    """The singular lemma of a plural group noun ('robbers'->'robber') via the
    held WordNet morphy — the SAME signal _grounded_number reads. Falls back to
    the surface unchanged when morphy does not lemmatise it."""
    try:
        from nltk.corpus import wordnet as wn
        lemma = wn.morphy(name, "n")
        if lemma and lemma != name:
            return lemma
    except Exception:
        pass
    return name


def _group_member(agent, group_node):
    """An already-individuated resident member of `group_node` (the SAME returning
    individual, reused across its run of pronouns), or None."""
    _, native = _resolve(agent)
    for m in native.in_neighbours(group_node, "member_of"):
        return m
    return None


def _individuate_member(agent, group_node, spec: dict, turn: int, mention, sentence: str):
    """Mint (or reuse) the singular MEMBER a singular pronoun bridges to. The member
    is animate, subject-salient, and carries a `member_of` edge to the group; a
    FeatureBelief(feature='member_of') records it as a WEAK reader inference so a
    later surprise can escalate/revise it. Mechanical graph I/O — the DECISION to
    bridge is the salience comparison in resolve_pronoun (the Argmax's scores)."""
    sub, native = _resolve(agent)
    existing = _group_member(agent, group_node)
    g_at = sub.node(group_node)["attrs"]
    g_name = g_at.get("name")
    if existing is not None:
        # the SAME individual continues its pronoun run: refresh salience only.
        sub.set_attr(existing, "coref_recency", float(turn))
        sub.set_attr(existing, "coref_rolerank", 0.0)
        return existing
    m_name = _singularize(str(g_name))
    if m_name == g_name:
        m_name = "one_of_" + str(g_name)
    nid = smr._entity(agent, m_name, unit=g_at.get("unit"))
    sub.set_attr(nid, "coref_category", g_at.get("coref_category") or "unknown")
    sub.set_attr(nid, "coref_number", "singular")
    sub.set_attr(nid, "coref_animate", 1.0)
    sub.set_attr(nid, "coref_cleanliness", 1.0)
    sub.set_attr(nid, "coref_gender", spec.get("gender") or "")
    sub.set_attr(nid, "coref_function_word", 0.0)
    sub.set_attr(nid, "coref_metrical_prominence", 0.0)
    sub.set_attr(nid, "coref_recency", float(turn))
    sub.set_attr(nid, "coref_rolerank", 0.0)          # the individual is the subject
    sub.set_attr(nid, "coref_mentions", 1.0)
    smr._edge(native, nid, "member_of", group_node)
    _belief_set(agent, m_name, "member_of", g_name, source=_SOURCE_READER,
                confidence=float(_SURPRISE_EV_W), turn=turn, established_by=mention)
    return nid


def propagate_member_participation(agent, unit=None) -> int:
    """A member's participation IS its group's (distributive reading): for every
    `M -member_of-> G`, MIRROR M's agent/theme/goal event edges onto G, so the
    opposition / co-participation Argmax counts a member's conflict ('the dog bit
    the [robber]') as the group's ('the dog opposes the robbers'). Idempotent
    mechanical graph I/O (adds an edge only when absent); returns the count added.
    Not a decision — a graph read that makes membership visible to the SAME
    Count/Intersect Term the antagonist Argmax already runs."""
    sub, native = _resolve(agent)
    added = 0
    for g in sub.nodes("SmEntity"):
        if unit is not None and sub.node(g)["attrs"].get("unit") != unit:
            continue
        members = list(native.in_neighbours(g, "member_of"))
        for m in members:
            for role in ("agent", "theme", "goal"):
                for e in native.in_neighbours(m, role):
                    if g not in set(native.neighbours(e, role)):
                        smr._edge(native, e, role, g)
                        added += 1
    return added


# --------------------------------------------------------------------------- #
#  THE RESOLUTION CALL.
# --------------------------------------------------------------------------- #
def resolve_pronoun(agent, surface: str, sentence: str, turn: int,
                     cb_name: Optional[str], unit=None,
                     exclude_name: Optional[str] = None) -> dict:
    """Resolve ONE pronoun occurrence: build the Argmax Program over the
    resident SmEntity pool, evaluate it NATIVELY, RI-Val the margin over the
    runner-up. A bind that fails validation is HELD OPEN (Mention flagged, no
    `refers_to` edge) — never forced. Mints the Mention node + edge as a side
    effect; returns the resolution trace.

    `exclude_name` enforces Binding Principle B (disjoint reference): a
    non-reflexive OBJECT pronoun is dropped from binding its own clause's SUBJECT
    ('the sparrow asked HIM' -> him != sparrow). Threaded into every candidate
    set here (main Argmax, runner-up margin, and the surprise probes) so the
    exclusion holds uniformly. `None` = the pre-Principle-B path (byte-identical)."""
    sub, native = _resolve(agent)
    spec = _PRONOUNS.get(surface.lower())
    mention = sub.add_node("SmMention", {"surface": surface, "sentence": sentence,
                                          "t": float(turn)})
    if spec is None:
        sub.set_attr(mention, "held_open", 1.0)
        sub.set_attr(mention, "reason", "not a covered pronoun form")
        return {"resolved": False, "surface": surface, "mention": smr._v(mention),
                "reason": "not a covered pronoun form"}

    # The pronoun's OWN gender (its lexical shape) enters the agreement spec so
    # the shape-MATCH Term rejects an entity of the established-opposite gender
    # (strict) while admitting an underspecified one (permissive).
    pron_g = gs.pronoun_gender(surface)
    spec = dict(spec)
    if pron_g:
        spec["gender"] = pron_g

    # SURPRISE (revisable feature belief). Alongside the gender-FILTERED winner,
    # find the pronoun's most-salient candidate under the gender-RELAXED filter.
    # If they DIFFER, the relaxed top is a MORE-salient entity the filter excluded
    # for carrying a CONFLICTING established gender -- a surprise
    # (prediction_minus_observation != 0). An explanation collapse (native Argmax)
    # decides who was wrong: the READER (mis-inferred that gender -> revise), the
    # writer/character (asserted it -> keep + flag), or the referent changed.
    # When relaxed == filtered there is no surprise and the path below is
    # byte-identical to the pre-belief behaviour.
    revision = None
    if pron_g:
        relaxed_spec = {k: v for k, v in spec.items() if k != "gender"}
        relaxed_winner = native.evaluate(
            antecedent_argmax_term(relaxed_spec, cb_name, unit, exclude_name), {})
        filtered_probe = native.evaluate(
            antecedent_argmax_term(spec, cb_name, unit, exclude_name), {})
        if relaxed_winner is not None and relaxed_winner != filtered_probe:
            rw = sub.node(relaxed_winner)["attrs"]
            rw_name = rw.get("name")
            if (rw.get("coref_gender") or "") == gs.opposite_gender(pron_g):
                cc = _belief_conflict_bump(agent, rw_name, "gender")
                verdict = _explain_surprise(agent, rw_name, "gender", cc)
                if verdict == "reader_wrong":
                    revision = _revise_reader_wrong(
                        agent, rw_name, "gender", pron_g, turn, cb_name, unit)
                elif verdict in ("writer_wrong", "character_wrong"):
                    bnid = _belief_find(agent, rw_name, "gender")
                    if bnid is not None:
                        sub.set_attr(bnid, "anomaly", 1.0)

    term = antecedent_argmax_term(spec, cb_name, unit, exclude_name)
    winner = native.evaluate(term, {})

    # BRIDGING ANAPHORA / SET-MEMBERSHIP (revisable). A singular animate pronoun
    # whose most-salient antecedent under a NUMBER-RELAXED filter is a PLURAL
    # animate GROUP — one the strict number filter (correctly) excluded, yet which
    # OUTSCORES the best surviving singular — denotes an INDIVIDUAL of that group
    # ("one of them ... he went ... the dog bit him"). Individuate the member and
    # bind to it. The SAME relaxed-vs-filtered probe idiom the gender surprise runs,
    # applied to NUMBER; recorded as a weak belief so a later conflict escalates.
    if spec.get("number") == "singular" and spec.get("agree") == "person":
        relaxed_num = dict(spec)
        relaxed_num["number"] = "any"     # keep animacy+gender, drop the number filter
        rn_winner = native.evaluate(
            antecedent_argmax_term(relaxed_num, cb_name, unit, exclude_name), {})
        if (rn_winner is not None
                and sub.node(rn_winner)["attrs"].get("coref_number") == "plural"):
            rn_score = float(native.evaluate(_score_term("e", cb_name), {"e": rn_winner}))
            strict_score = (float(native.evaluate(_score_term("e", cb_name), {"e": winner}))
                            if winner is not None else -1e18)
            if rn_score > strict_score:
                g_name = sub.node(rn_winner)["attrs"].get("name")
                member = _individuate_member(agent, rn_winner, spec, turn, mention, sentence)
                smr._edge(native, mention, "refers_to", member)
                sub.set_attr(mention, "held_open", 0.0)
                return {"resolved": True, "surface": surface,
                        "mention": smr._v(mention),
                        "concept": sub.node(member)["attrs"].get("name"),
                        "entity": member, "bridged": True, "group": g_name,
                        "margin": rn_score - strict_score,
                        "rule": ("bridging: '%s' individuated as a member_of the "
                                 "salient plural group '%s' (number-relaxed group "
                                 "outscored the best singular) — revisable"
                                 % (surface, g_name))}

    if winner is None:
        reason = (f"no resident SmEntity agrees with '{surface}' "
                  f"({spec['agree']}/{spec['number']}"
                  f"{'/' + pron_g if pron_g else ''}) -- gender-shape incompatible")
        sub.set_attr(mention, "held_open", 1.0)
        sub.set_attr(mention, "reason", reason)
        return {"resolved": False, "surface": surface, "mention": smr._v(mention),
                "reason": reason}

    winner_name = sub.node(winner)["attrs"]["name"]
    winner_score = float(native.evaluate(_score_term("e", cb_name), {"e": winner}))
    runner_source = _Filter(
        candidate_term(spec, unit, exclude_name), "e2",
        _Not(_Eq(_Attr(_V("e2"), "name"), _Lit(winner_name))))
    runner_score = float(native.evaluate(
        _MaxOver(runner_source, "e2", _score_term("e2", cb_name), default=_Lit(-1e18)),
        {}))
    margin = winner_score - runner_score

    if margin < _MARGIN_EPS:
        reason = (f"ambiguous: top candidate '{winner_name}' leads the runner-up "
                  f"by only {margin:.3f} (< {_MARGIN_EPS}) -- HELD OPEN, not "
                  "force-bound (RI-Val validation)")
        sub.set_attr(mention, "held_open", 1.0)
        sub.set_attr(mention, "reason", reason)
        return {"resolved": False, "surface": surface, "mention": smr._v(mention),
                "top_candidate": winner_name, "margin": margin, "reason": reason}

    # BIND — the Argmax's own verdict; Python performs the mechanical edge write.
    smr._edge(native, mention, "refers_to", winner)
    sub.set_attr(mention, "held_open", 0.0)

    # CONTEXT DEQUANT (the sd-loop mint) — the FIRST gendered pronoun to LAND on
    # an underspecified animate entity DEQUANTIZES its gender: the ass 'he' ->
    # male, established from the story's own pronoun use. This is the DYNAMIC
    # axis — the same word takes a different gender in a different tale. Only an
    # UNDERSPECIFIED gender is filled (a decoded natural/prior gender, or one
    # already established by an earlier pronoun, is never overwritten); every
    # later pronoun BINDS by the graph-native shape-MATCH above (strict).
    dequantized = False
    matched_established = False
    if pron_g:
        cur_g = sub.node(winner)["attrs"].get("coref_gender") or ""
        if not cur_g or cur_g == "unknown":
            # WEAK reader-inference: this bind is the sole evidence, its
            # confidence is the salience MARGIN it won by, and the Mention that
            # set it is recorded so a later surprise can retroactively rebind it.
            _belief_set(agent, winner_name, "gender", pron_g,
                        source=_SOURCE_READER, confidence=float(margin),
                        turn=turn, established_by=mention)
            dequantized = True
        elif cur_g == pron_g:
            matched_established = True
            _belief_bump(agent, winner_name, "gender", turn)

    if winner_name == cb_name:
        rule = "centering_rule_1 (Cb = %s)" % cb_name
    elif dequantized:
        rule = ("salience (role-rank + recency); gender-dequant establishes %s "
                "(context: the '%s' pronoun decodes the animate entity's gender)"
                % (pron_g, surface))
    elif matched_established:
        rule = "salience (role-rank + recency); gender-shape match (established %s)" % pron_g
    else:
        rule = "salience (role-rank + recency; gender not grounded)"
    return {"resolved": True, "surface": surface, "mention": smr._v(mention),
            "concept": winner_name, "entity": winner, "rule": rule, "margin": margin,
            "gender": pron_g, "gender_dequantized": dequantized,
            "gender_matched": matched_established, "revision": revision}


# --------------------------------------------------------------------------- #
#  per-predication driver — resolve pronoun ARGS, then hand off UNCHANGED.
# --------------------------------------------------------------------------- #
def _predication_roles(agent, pred: list) -> list:
    """[(role, arg), ...] for a [rel, a0, a1] predication. arg0 is always the
    subject slot ("agent"); arg1's role is READ from the situation_model rule's
    OWN frame (smr.cos_membership + smr._verb_frames, the SAME lookup
    ingest_predication performs) — consulted early, not re-derived, so pronoun
    resolution ranks candidates by the correct grammatical role BEFORE
    ingest_predication mints/updates the model."""
    if not pred or len(pred) < 2:
        return []
    rel, a0 = str(pred[0]), str(pred[1])
    roles = [("agent", a0)]
    if len(pred) > 2:
        a1 = str(pred[2])
        if smr._is_property_pred(rel.lower()):
            roles.append(("attribute", a1))
        else:
            mem = smr.cos_membership(agent, rel)
            obj_role = "theme"
            if mem["cos"]:
                frame = smr._verb_frames().get(mem["canon"], {"theme"})
                obj_role = "goal" if "goal" in frame else "theme"
            roles.append((obj_role, a1))
    return roles


# --------------------------------------------------------------------------- #
#  METRICAL-VERSE GATE + HERO LICENSING (the PINCER). The verse gate is a PURE
#  perceptual read (metrical_reading's held-phonology stress scan + the temporal-
#  harmonic autocorrelation confident-beat verdict) — NO graph mutation, NO
#  decision over graph state. It only decides WHERE prominence may be SET; the
#  antecedent DECISION stays the graph-native Argmax (the prominence FACTOR).
# --------------------------------------------------------------------------- #
def _text_is_verse(agent, text: str) -> bool:
    """Is `text` metrical VERSE? SUPERSEDED by the generic FORMAT CHANNEL: verse is
    now ONE format the reader recognizes (PROSODY), not the default reading of any
    multi-line block. This delegates to `format_channel.is_prosody` — the ShapeDecode
    collapse over the format-function codebook — so the verse gate fires ONLY when
    the layout's FUNCTION is prosody (voluntary short breaks tracking a regular
    rhyme scheme), NOT when a hard-wrapped MEDIUM file merely has short-ish lines
    (the Grimm-wrap misdetection this replaces). The DECISION is the graph collapse,
    not a Python line-length/meter-fraction heuristic."""
    from domains import format_channel as fc
    try:
        return fc.is_prosody(agent, text)
    except Exception:
        return False


def _license_metrical_hero(agent, pred: list, sentence: str, turn: int, *, unit=None):
    """In a VERSE text, the metrically-prominent AGENT is the salient referent.
    When a clause's SUBJECT (arg0) is a person-pronoun ('he'/'she'/'they'), the
    pronoun-only hero has no proper-noun anchor and the flat salience ranking
    mislabels it as the salient-but-wrong first-antecedent. This mint-or-fetches
    a PERSISTENT protagonist entity keyed by the pronoun surface, tags it
    metrically prominent (coref_metrical_prominence = 1.0) and person-category,
    so the graph-native Argmax (which now carries the prominence FACTOR) binds
    every hero pronoun to ONE licensed protagonist instead of the recency
    artefact. Mechanical adapter I/O (mint-or-fetch + attr writes); the CHOICE
    stays the Argmax."""
    if not pred or len(pred) < 2:
        return
    a0 = str(pred[1]).lower()
    spec = _PRONOUNS.get(a0)
    if spec is None or spec.get("agree") != "person":
        return
    sub, _native = _resolve(agent)
    nid = _touch_entity(agent, sentence, a0, "agent", turn, unit=unit)
    sub.set_attr(nid, "coref_metrical_prominence", _PROMINENT)
    sub.set_attr(nid, "coref_category", "person")   # a person-pronoun hero — 'it' must reject it
    if spec.get("number") == "plural":
        sub.set_attr(nid, "coref_number", "plural")


def resolve_and_ingest(agent, pred: list, sentence: str, turn: int, unit=None, *,
                       verse: bool = False) -> dict:
    """Resolve every pronoun ARGUMENT of `pred` to a resident SmEntity, mint the
    `Mention --refers_to--> SmEntity` edge (or HOLD OPEN), substitute the
    resolved name in place, update coref bookkeeping + Cf/Cb for every entity
    realized this turn, then hand the (possibly substituted) predication to
    situation_model_reader.ingest_predication — UNCHANGED, reused as-is, so the
    state change lands on the resolved protagonist."""
    cb_name = _current_cb(agent)
    # VERSE PINCER: license the metrically-prominent hero BEFORE the Argmax, so
    # the graph-native prominence FACTOR (not a Python override) binds the hero
    # pronoun to ONE licensed protagonist. Only fires in a verse text (prose is
    # never `verse` — the crow path is untouched, byte-identical).
    if verse:
        _license_metrical_hero(agent, pred, sentence, turn, unit=unit)
    # SPEECH-ACT INVERSION — ONLY the narrow \"'quote' said the sparrow\" case, where
    # the QUOTED CONTENT sits in the subject slot and the real speaker is post-posed.
    # Re-collapse it to [verb, speaker] so the speaker is the agent and the quoted
    # epithet ('wretch') is NOT minted as a referent (that spawned the spurious
    # 'wretch' person entity that stole coref weight). Every normal speech act
    # ('the sparrow said to him', 'told the dog ...') returns None and is UNTOUCHED.
    inv = _quoted_subject_inversion(agent, pred, unit=unit)
    if inv is not None:
        pred = [pred[0], inv[0]]                    # keep only the speaker

    roles = _predication_roles(agent, pred)
    resolutions = []
    new_pred = list(pred)
    for i, (role, arg) in enumerate(roles):
        surface = arg.lower()
        # DEIXIS FIRST — a first/second-person form points at the deictic centre
        # (speaker/addressee), NOT a salient antecedent, so it is bound DIRECTLY and
        # NEVER enters the salience Argmax (that is what let 'I' spawn a 'wretch'
        # entity). Substituting the resolved speaker name folds a self-predication
        # ('unlucky wretch that I am' -> is_a(carter, wretch)) onto the real speaker.
        if role != "attribute" and surface in _DEIXIS:
            rec = _resolve_deixis(agent, surface, _DEIXIS[surface], sentence, turn)
            resolutions.append(rec)
            if rec["resolved"]:
                new_pred[i + 1] = rec["concept"]
        elif role != "attribute" and surface in _PRONOUNS:
            # BINDING PRINCIPLE B (disjoint reference): a non-reflexive OBJECT
            # pronoun (any slot past the subject) cannot co-refer with its own
            # clause's SUBJECT (arg0, now resolved in new_pred[1]). Excluding it
            # stops 'the sparrow asked HIM' from binding 'him' back onto 'sparrow'
            # (the bind that dequantised the sparrow male). The subject slot itself
            # (i == 0) passes exclude_name=None -> byte-identical there.
            exclude = new_pred[1] if i > 0 and len(new_pred) > 1 else None
            rec = resolve_pronoun(agent, surface, sentence, turn, cb_name, unit,
                                  exclude_name=exclude)
            resolutions.append(rec)
            if rec["resolved"]:
                new_pred[i + 1] = rec["concept"]

    # PROPER-NAME SPAN COMPLETION (Phase 3): a multi-token proper name
    # ('Robert Levy') is ONE entity keyed by its FULL span (see
    # `_proper_name_span`'s docstring for the decision + the held ablation
    # gate). Runs AFTER pronoun/deixis substitution (an already-resolved
    # concept name is idempotent under it — it always carries an underscore
    # or fails the proper-noun test) and BEFORE bookkeeping/ingest below, so
    # `_touch_entity` and `situation_model_reader.ingest_predication` both
    # see the SAME full-span name — one entity, not a truncated head plus an
    # orphaned appositive.
    for i, (role, arg) in enumerate(_predication_roles(agent, new_pred)):
        if role == "attribute":
            continue
        ext = _proper_name_span(agent, sentence, arg)
        if ext != arg:
            new_pred[i + 1] = ext

    # bookkeeping AFTER substitution — roles now point at resolved names.
    realized = {}
    for role, arg in _predication_roles(agent, new_pred):
        if role == "attribute":
            continue
        _touch_entity(agent, sentence, arg, role, turn, unit=unit)
        realized[arg] = role
    _update_centering(agent, realized, turn)

    ing = smr.ingest_predication(agent, new_pred, t=turn, unit=unit)
    return {"predication": pred, "resolved_predication": new_pred,
            "resolutions": resolutions, "ingest": ing}


# --------------------------------------------------------------------------- #
#  READ TEXT, COREFERENCE-ENABLED — the driver: reader -> resolve -> ingest.
# --------------------------------------------------------------------------- #
def read_into_situation_model(agent, text: str, *, max_sentences: int = 40, unit=None,
                              flow_node=None, register=None) -> dict:
    """THE WIRE, coreference-enabled. Segment `text`, read each sentence (the
    HELD reading_scope.read_scope, reused as-is; rc.read_clause fallback for a
    held-open scope — the SAME fallback situation_model_reader.
    read_into_situation_model uses), resolve every pronoun argument to a
    resident SmEntity via the Centering/salience Argmax BEFORE minting state,
    then hand off to situation_model_reader.ingest_predication (unchanged).
    Returns the textbase, the per-mention resolution trace, and the situation
    model (read back from SmEntity, exactly as the unwired reader does).

    THIS IS THE LIVE READING SPINE (Wave: dynamic-thresholds/reopen/reform,
    2026-07-11) — "the reopen is the entire point of the circular buffer and
    was already in place for extended reading" (the user's directive): the
    ring buffer (reading_scope.enforce_trace_buffer) is now bounded HERE,
    after every commit, to an EFFECTIVE capacity derived from this flow's own
    register + overflow pressure (domains/reading_norms), flow-scoped via
    `unit` so RetainedTrace nodes carry a `flow` stamp and a persistent
    substrate's other flows never evict or count toward this one's ring. A
    NON-SEQUITUR between two successive committed sentences (no shared
    referent — the SAME signal read_paragraph already reanalyses on)
    REACTIVATES the still-resident retained trace first (warm — no re-
    derivation) and only falls back to a cold `_reread_from_source` when the
    ring has already wrapped it out, bounded by the held max_revisits budget.
    `flow_node`/`register` are optional (mechanical passthrough from
    reading_drive._shim_spine): when absent (a bare unit-test caller with no
    run_reading_flow behind it) the ring still bounds+reopens, just unscoped
    and against the Python literal defaults — byte-identical to every
    pre-wave caller of this function that never passed them."""
    smr.ensure_seeds(agent)
    sub, native = _resolve(agent)
    from domains import reading_norms as rn
    # FORMAT CHANNEL — decode the text's LAYOUT as a signal PARALLEL to its content
    # (format_channel.reflow runs the ShapeDecode collapse over the format-function
    # codebook, records a Format node, and returns the verdict). The verdict DRIVES
    # perception: PROSODY keeps its line breaks (format-AS-content -> the metrical
    # hero may license); MEDIUM/REGISTER newlines are SOFT display artefacts, so the
    # AGENT reflows the wrapped lines into flowing prose for comprehension. The world
    # adapter (corpus loader) NEVER unwraps -- the unwrap is the agent's own read of
    # the format, exactly as the verse gate was a perceptual read. `verse` (prosody)
    # is now the ShapeDecode verdict, not a Python line-length heuristic.
    from domains import format_channel as fc
    fmt = fc.reflow(agent, text)
    verse = fmt["is_prosody"]
    text = fmt["text"]
    sentences = rc._split_sentences(text)
    textbase: list = []
    resolutions: list = []
    ingests: list = []
    reanalyses: list = []
    prior_committed: Optional[dict] = None
    turn = 0
    for s in sentences[:max_sentences]:
        if not s.strip():
            continue
        rec = rs.read_scope(agent, s, unit=unit)
        preds = rec.get("predications") or []
        source = "read_scope"
        if not preds:
            # ARGUMENT-STRUCTURE FALLBACK — a held-open single clause whose SUBJECT is
            # inverted (OSV / VS / fronted-adjunct: 'Into the room walked a tall man',
            # 'Slowly he rose') is parsed by the held argument-structure binder (role
            # by case + inversion, not position) BEFORE dropping to read_clause. The
            # binder ABSTAINS on a construction-marked clause (copular/subordinated),
            # so read_clause's territory is untouched.
            inv = rc.event_predication_for_sentence(agent, s)
            if inv:
                preds = inv
                source = "argstruct_fallback"
            else:
                fb = rc.read_clause(agent, s, write=False)
                preds = fb.get("predications") or []
                source = "read_clause_fallback"
        # COMPLEXITY MEASUREMENT (Wave: dynamic-thresholds/reform) — two mechanical
        # signals a reform RULE (seeds/reading_aperture.json's reform_overcomplex_
        # clause) compares against a held threshold. `residual_marker_count` is a
        # TRIAL run of reading_collapse.read_clause_order_n at the BASE order
        # (write=False/learn=False — a pure measurement, the SAME 'shadow' cost
        # tier the shadow-read comprehension battery already pays): how many
        # component (part_of/marker) predications an order-N descent WOULD
        # produce right now — an enumeration ('a battery, a screen, a camera')
        # or compound-tail clause measures >0 even when its order-1 `residual`
        # is empty (the winning construction already covers the marker), a
        # plain SVO clause measures 0 either way. `swallowed_ratio` (reading_
        # scope.swallowed_ratio, factored out of _assembled_incoherence for
        # exactly this reuse) is the SECOND, independent signal.
        try:
            _trial = rc.read_clause_order_n(agent, s, max_order=2, write=False, learn=False)
            # ONLY the enumeration-list / compound-tail descents count as genuine
            # extra STRUCTURE — the third descent kind (`pair_clean_head`) fires
            # unconditionally for every 2-role pair/pair_swap clause (it just
            # restates the SAME predication with a cleaned head), so counting it
            # would make every plain transitive SVO clause measure >0 and violate
            # "a simple clause must never trigger reform".
            residual_marker_count = len(_trial.get("members") or []) + len(_trial.get("compound_tail") or [])
        except Exception:
            residual_marker_count = 0
        swallowed = rs.swallowed_ratio(preds)
        trace_node = rec.get("trace_node") if rec.get("committed") else None
        textbase.append({"sentence": s, "predications": preds, "source": source,
                         "residual_marker_count": residual_marker_count,
                         "swallowed_ratio": swallowed, "trace_node": trace_node})
        # DEICTIC CENTRE — re-collapse WHO is speaking from this sentence's speech-act
        # tag BEFORE resolving its predications, so a first-person form in the quoted
        # span binds to the speaker even when the tag ('cried he') FOLLOWS the quote.
        # A no-op (centre carried forward, or absent) when the sentence has no tag.
        _update_deictic_centre(agent, preds, turn + 1, unit=unit)
        for p in preds:
            turn += 1
            out = resolve_and_ingest(agent, p, s, turn, unit=unit, verse=verse)
            resolutions.extend(out["resolutions"])
            ingests.append(out["ingest"])
            # SALIENT ORDER-N CACHE hook (opt-in): if the salient_cache seed is
            # installed on this agent, refresh the working memory for this
            # predication's (coref-resolved) entities and advance one tick so the
            # rise/decay/promote RULES fire and mirror story-salience onto the
            # SmEntities BEFORE the next predication's pronoun Argmax reads it.
            # A no-op when the cache is absent (the crow / every existing test) —
            # so those paths are byte-identical. Mechanical adapter I/O (mark the
            # cells observed, advance the clock, run_rules); no decision here.
            _salient_cache_tick(agent, out.get("resolved_predication") or p, turn, unit)

        # THE RING, LIVE (Wave: dynamic-thresholds/reopen) — bound the retained
        # buffer to this flow's own EFFECTIVE capacity after every commit (never
        # only at paragraph end, per the directive: "the reopen is the entire
        # point of the circular buffer"). `widened` is a mechanical read of the
        # flow's own Source.capacity_widened (set by the reading_widen_capacity_
        # once RULE on eviction pressure, never decided here).
        if rec.get("committed"):
            widened = False
            if flow_node is not None:
                widened = float(sub.node(flow_node)["attrs"].get("capacity_widened", 0.0) or 0.0) >= 1.0
            capacity = rn.effective_trace_capacity(agent, register, widened=widened)
            evicted = rs.enforce_trace_buffer(agent, capacity, unit=unit)
            if flow_node is not None:
                for ev in evicted:
                    try:
                        sal = float(sub.node(ev)["attrs"].get("salience", 0.0) or 0.0)
                    except Exception:
                        sal = 0.0
                    rn.record_eviction_pressure(sub, flow_node, sal)

            # THE REOPEN — a NON-SEQUITUR (this commit shares no referent with the
            # prior commit) REACTIVATES the prior's still-resident retained trace
            # first (warm — reading_scope.reactivate re-collapses from the RETAINED
            # lattice, no re-derivation); reading_scope._reanalyse falls back to the
            # cold `_reread_from_source` only when the ring already evicted it. This
            # is the SAME mechanism read_paragraph already runs at paragraph scope,
            # now wired into the LIVE per-sentence spine (the "already in place for
            # extended reading" the directive names), bounded by the held revisit
            # budget.
            if prior_committed is not None and prior_committed.get("committed"):
                if not rs._coheres_across(prior_committed["referents"], rs._referents(preds)):
                    max_revisits = rn.effective_max_revisits(agent, register)
                    reanalyses.append(rs._reanalyse(agent, prior_committed, rec, max_revisits))
            prior_committed = rec

    # AGENCY IMPLIES ANIMACY — re-ground eventive-agent characters mis-categorised
    # object/unknown by the patient-slot first-mention grounding. Byte-identical on
    # a short fable whose agents already ground animal (they are skipped by (a)).
    animacy_rewrites = _refine_animacy_from_agency(agent, textbase, unit=unit)

    model: dict[str, dict] = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if unit is not None and at.get("unit") != unit:
            continue
        if nm:
            model[nm] = {k: v for k, v in at.items() if k != "name"}
    return {"text": text, "sentences": sentences, "textbase": textbase,
            "resolutions": resolutions, "ingests": ingests, "situation_model": model,
            "animacy_rewrites": animacy_rewrites, "reanalyses": reanalyses,
            "n_reanalyses": len(reanalyses)}


def _salient_cache_tick(agent, pred, turn: int, unit=None) -> None:
    """Advance the SALIENT ORDER-N CACHE by one tick for `pred`'s entities — a
    thin opt-in hook. No-op unless the salient_cache seed is installed (checked
    in salient_cache.after_predication, which returns immediately when the
    SalienceClock is absent), so the crow / every existing test path is
    byte-identical. Mechanical adapter I/O; the salience DECISION is the seed's
    rise/decay/promote RULES."""
    try:
        from domains import salient_cache as sc
    except Exception:
        return
    try:
        sc.after_predication(agent, pred, turn, unit=unit)
    except Exception:
        pass


__all__ = [
    "resolve_pronoun", "resolve_and_ingest", "read_into_situation_model",
    "antecedent_argmax_term", "candidate_term", "arm_deictic_centre",
]

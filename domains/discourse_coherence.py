"""discourse_coherence — COHERENCE RELATIONS + CAUSAL-NETWORK CENTRALITY.

The reader (`reading_collapse` / `situation_model_reader` / `coref_entities` /
`inference_generation`) builds a Kintsch textbase, binds pronouns, and infers
unstated facts WITHIN and slightly ACROSS sentences. It has no representation
of the relation BETWEEN two committed spans (elaboration / contrast / cause /
sequence / condition) and no notion of which events are CENTRAL to the story
— the substrate a SUMMARY would read off. This module is that missing layer,
built the same way reading_collapse reads a clause: COLLAPSE, one level up.

  1. COHERENCE RELATION = ShapeDecode over a DEDICATED codebook. A span-pair's
     coherence is decided by decoding a skeleton (a single marker token) against
     held `ShapeSignatureCoherence` nodes (`seeds/coherence_relations.json`) — a
     SEPARATE codebook_type from reading_collapse's clause-construction
     `ShapeSignature` pool (the same separation `ink_decode.py` uses for its
     `ShapeSignatureCoarse` codebook), so a coherence relation never competes
     with a clause construction. The skeleton token comes from ONE of two
     triggers — both are MECHANICAL READS off held graph data, never a Python
     if/else naming the relation itself:

       a. MARKED — a discourse connective recognised at the LEADING position of
          the second span, via the SAME marker-lexicon mechanism reading_collapse
          uses for clause markers (`reading_collapse._marker_lexicon`), reading
          the NEW discourse-cue MarkerClasses (DISC_CONTRAST / DISC_CAUSE /
          DISC_SEQUENCE / DISC_CONDITION, plus the EXISTING clause-level IF
          class, reused as-is).

       b. UNMARKED — a situation-model-STYLE signal read off the two spans' own
          grounded predications (`reading_collapse.read_clause`, reused as-is):
          shared entity (continuity — Centering Theory's preserved centre) plus
          either (i) spanA's verb is a change-of-state verb (the COS class,
          `situation_model_reader.cos_membership`, reused as-is — a PHYSICAL
          state delta), or (ii) spanB's verb is a TELIC_RESULT achievement verb
          (the new class mirroring COS/DESIGNATE/POSSESS's join-by-adjacency
          idiom) — either promotes the signal to SM_CAUSE; continuity alone is
          SM_SEQUENCE; spanB itself being a property-description construction
          (definitional/attributive/possession/designation) is SM_ELABORATE.

     Either way the SAME `_decode` call (a thin `ShapeDecode` Term, mirroring
     `reflective_faculty.compose_design_for_goal`'s shim but pointed at the
     coherence codebook_type) reads off the winning ShapeSignatureCoherence's
     `relation` attr — the decode decides, this module only feeds it a token
     and reads its verdict.

  2. CENTRALITY = WEIGHTED node degree over the causes/enables/before/
     coherence_rel graph (Trabasso & van den Broek's causal-network model:
     central events have the most CAUSAL connections — a genuine causal or
     enabling antecedent-consequent link, not just any coherence relation of
     any kind). Every decoded span-pair mints a `coherence_rel` edge (always)
     plus a `causes` edge (relation == "cause") or a `before` edge (relation in
     {"sequence","condition"}) between the spans' `DiscourseEvent` nodes;
     `comprehension_reader`'s goal-action-enabling pass additionally mints
     `enables` edges over the SAME node type (goal sentence -> action sentence
     -> next action sentence) — mechanical translation of already-decided
     facts into graph data, not a new decision. Degree is a WEIGHTED Term-tree
     (`Times(weight, Count(Neighbours))` + `Times(weight, Count(InNeighbours))`
     per edge type, summed by `Plus` — the SAME `Count`/`Neighbours`/`Times`
     idiom `gap_prioritiser.payoff_term` / `coref_entities._score_term` already
     compose): `causes`/`enables` (a genuine causal/enabling link) carry
     `_CAUSAL_WEIGHT`, `before`/`coherence_rel` (temporal order, or ANY
     decoded relation including contrast/elaboration) carry the lower
     `_NONCAUSAL_WEIGHT` — a causal connection outweighs a bare 'then'/'but'
     sequence/contrast tie, per the module's whole point. The WINNER (the
     single most-central node) is picked by `Argmax` over
     `NodesOfType("DiscourseEvent")` on this weighted degree — a graph-native
     decision, never Python's `max()`/`sorted()`. A full descending ranking for
     DISPLAY additionally uses Python `sorted()` — the SAME precedent
     `gap_prioritiser.rank_gaps` already establishes (Argmax decides the
     winner; `sort()` only orders the print), verified here to agree with the
     Argmax pick.

ARCHITECTURE (CLAUDE.md). The coherence-relation DECISION is the ShapeDecode
Term's verdict (read off its `plan`, via the SAME `_winner` read-off
`reading_collapse._winner` uses — reused directly, not reimplemented); the
CENTRALITY decision is the `Argmax` Term's verdict. This module only (a) reads
markers/predications/verb-classes off already-existing held faculties
(mechanical), (b) builds the skeleton token + the Term-trees (data), (c) mints
the resulting edges (mechanical graph I/O), (d) reads the decode's/Argmax's
result back out. No `import re`, no per-relation Python if/else naming a
relation, no Python loop counting edges, no Python max()/sorted() picking the
central node.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import reading_collapse as rc
from domains import situation_model_reader as smr

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "coherence_relations.json")

_CODEBOOK_TYPE = "ShapeSignatureCoherence"

# discourse-connective classes recognised at the leading position of the SECOND
# span (marked trigger). "IF" is the EXISTING clause-level class (reused as-is).
_DISC_CLASSES = {"DISC_CONTRAST", "DISC_CAUSE", "DISC_SEQUENCE", "DISC_CONDITION", "IF"}

# reading_collapse construction names whose predication is a PROPERTY of an
# entity, not a new event -- the elaboration signal's construction test.
_PROPERTY_CONSTRUCTIONS = {"definitional", "definitional_bare", "attributive",
                           "possession", "designation"}

# causal-network edge types the centrality degree sums over, WEIGHTED by type:
# `causes` (physical-causal, minted here or by inference_generation.
# resolve_causal_gap) and `enables` (the goal-action-enabling chain minted by
# comprehension_reader) are genuine CAUSAL antecedent-consequent links — the
# strongest coherence relation in Trabasso & van den Broek's model. `before`
# (temporal sequence/condition) and `coherence_rel` (the relation-tagged edge
# EVERY decoded pair carries, including non-causal contrast/elaboration) are
# weaker, non-causal discourse ties. Weighting causal >> non-causal is itself
# a graph-native Term (`Times` in `_degree_term`, below) — never a Python
# multiply-then-compare.
_CAUSAL_EDGE_TYPES = ("causes", "enables")
_NONCAUSAL_EDGE_TYPES = ("before", "coherence_rel")
_CAUSAL_WEIGHT = 3.0
_NONCAUSAL_WEIGHT = 1.0
_EDGE_WEIGHTS = {et: _CAUSAL_WEIGHT for et in _CAUSAL_EDGE_TYPES}
_EDGE_WEIGHTS.update({et: _NONCAUSAL_WEIGHT for et in _NONCAUSAL_EDGE_TYPES})
_FABULA_EDGE_TYPES = _CAUSAL_EDGE_TYPES + _NONCAUSAL_EDGE_TYPES


# --------------------------------------------------------------------------- #
#  resolution + codebook install (mechanical adapter I/O — no decision).
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


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def ensure_codebook(agent) -> None:
    """Idempotently install the coherence-relation codebook (the discourse-cue
    MarkerClasses + TELIC_RESULT + the ShapeSignatureCoherence nodes) plus its
    dependency (reading_constructions, for the marker-lexicon mechanism + the
    EXISTING IF class) and situation_model_reader's own seeds (for cos_membership
    reuse). Guarded by a graph-resident `Seed` sentinel, the SAME idempotency
    idiom `reading_collapse.ensure_codebook` uses. Mechanical seed I/O."""
    sub, native, ag_node = _resolve(agent)
    smr.ensure_seeds(agent)             # reading_constructions + situation_model + event_reasoning
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "coherence_relations":
            return
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "coherence_relations", "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  MARKED — leading-marker recognition, the SAME lexicon mechanism reading_
#  collapse uses for clause markers, over the NEW discourse-cue classes.
# --------------------------------------------------------------------------- #
def _leading_marker(agent, span_text: str) -> tuple[Optional[str], Optional[str]]:
    """The discourse-connective CLASS (+ surface) at the leading position of
    `span_text`, or (None, None). Recognition against held `MarkerClass` data
    (`reading_collapse._marker_lexicon`) — no regex, no hardcoded word check."""
    sub, _, _ = _resolve(agent)
    words = ct._recognise_words(agent, span_text)
    lex = rc._marker_lexicon(sub)
    for w in words[:2]:
        cls = lex.get(w.lower())
        if cls in _DISC_CLASSES:
            return cls, w
    return None, None


# --------------------------------------------------------------------------- #
#  SPAN INFO — the span's grounded predications, entity set, construction, and
#  main-verb class, all read off HELD faculties (reading_collapse, reused as-is).
# --------------------------------------------------------------------------- #
def _span_info(agent, span_text: str) -> dict:
    sub, _, _ = _resolve(agent)
    words = ct._recognise_words(agent, span_text)
    _, _, marker_seq = rc._skeleton_from_words(agent, words)
    read = rc.read_clause(agent, words, write=False, learn=False)
    preds = read.get("predications") or []
    args: set = set()
    for p in preds:
        for a in p[1:]:
            args.add(a)
    verb = None
    for cls, w in marker_seq:
        if cls == "VERB":
            verb = w
    lex = rc._marker_lexicon(sub)
    verb_cls = lex.get(verb.lower()) if verb else None
    cos = smr.cos_membership(agent, verb) if verb else {"cos": False}
    return {"text": span_text, "predications": preds, "args": args,
            "construction": read.get("construction"), "verb": verb,
            "verb_cls": verb_cls, "cos": bool(cos.get("cos"))}


# --------------------------------------------------------------------------- #
#  UNMARKED — the situation-model-style signal: shared entity (continuity) +
#  spanA change-of-state OR spanB telic-result verb (-> cause), continuity alone
#  (-> sequence), spanB a property-description of a shared entity (-> elaborate).
# --------------------------------------------------------------------------- #
def _lexical_tokens(args: set) -> set:
    """Word-level tokens underlying a span's grounded arguments — a multi-word
    argument ('pebbles_in_the_pitcher', the residue of a preposition
    reading_collapse's clause skeleton does not split on) still carries its
    HEAD NOUNS as tokens. Shared-token overlap is Halliday + Hasan's LEXICAL
    COHESION (repetition/collocation holding text together,
    `seeds/ling_discourse.json`'s `lexical_cohesion` concept) — the mechanical,
    graph-adjacent continuity signal; not fuzzy string matching, a plain word
    split on the SAME underscore-join `reading_collapse._norm` already uses."""
    toks: set = set()
    for a in args:
        toks.update(str(a).split("_"))
    return toks


def _unmarked_signal(a_info: dict, b_info: dict) -> tuple[Optional[str], str]:
    shared = _lexical_tokens(a_info["args"]) & _lexical_tokens(b_info["args"])
    if not shared:
        return None, "no shared entity/lexical-cohesion token between spans"
    if b_info["construction"] in _PROPERTY_CONSTRUCTIONS:
        return ("SM_ELABORATE", "spanB is a property-description (construction=%r) of "
                "the shared entity %r" % (b_info["construction"], sorted(shared)))
    if a_info["cos"] or b_info["verb_cls"] == "TELIC_RESULT":
        return ("SM_CAUSE", "shared entity %r + spanA change-of-state=%s / spanB "
                "telic-result-verb=%r" % (sorted(shared), a_info["cos"], b_info["verb_cls"]))
    return "SM_SEQUENCE", "shared entity %r, temporal succession, no stronger cue" % sorted(shared)


# --------------------------------------------------------------------------- #
#  DECODE — a thin ShapeDecode shim pointed at the coherence codebook_type (kept
#  SEPARATE from reading_collapse's clause-construction ShapeSignature pool, the
#  same separation domains/ink_decode.py uses for ShapeSignatureCoarse).
# --------------------------------------------------------------------------- #
def _decode(agent, skeleton: list) -> dict:
    _, native, _ = _resolve(agent)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [list(x) for x in (skeleton or [])]},
            "codebook_type": _CODEBOOK_TYPE, "beam": 1, "max_steps": 1, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton or []), "ordered_parts": []}
    return res


def _relation_for(agent, name: str) -> Optional[str]:
    sub, _, _ = _resolve(agent)
    for n in sub.nodes(_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get("relation")
    return None


# --------------------------------------------------------------------------- #
#  ONE SPAN-PAIR — the whole decision: marker (if any) else unmarked signal,
#  decode, read off the relation.
# --------------------------------------------------------------------------- #
def coherence_between(agent, span_a: str, span_b: str) -> dict:
    """Decode the coherence relation holding between two adjacent spans. Returns
    {spanA, spanB, trigger, skeleton, construction, relation, shape_fit, note}.
    WHICH relation is `_decode`'s (ShapeDecode's) verdict; this only builds the
    skeleton token from a marker or the situation-model-style signal."""
    ensure_codebook(agent)
    marker_cls, marker_word = _leading_marker(agent, span_b)
    if marker_cls is not None:
        skeleton = [[marker_cls]]
        trigger = "marked:%s(%s)" % (marker_cls, marker_word)
        sig_note = "leading discourse connective %r recognised as class %r" % (marker_word, marker_cls)
    else:
        a_info = _span_info(agent, span_a)
        b_info = _span_info(agent, span_b)
        token, sig_note = _unmarked_signal(a_info, b_info)
        if token is None:
            return {"spanA": span_a, "spanB": span_b, "trigger": "none", "skeleton": [],
                    "construction": None, "relation": None, "shape_fit": 0, "note": sig_note}
        skeleton = [[token]]
        trigger = "unmarked:%s" % token
    res = _decode(agent, skeleton)
    plan = res.get("plan") or []
    name, fit = None, -1
    for p in plan:
        try:
            f = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            f = 0
        if f > fit:
            fit, name = f, p.get("part")
    relation = _relation_for(agent, name) if (name and fit > 0) else None
    note = (sig_note + (" -> decoded construction %r (fit %d) -> relation %r"
                        % (name, fit, relation) if relation else " -> no covering relation"))
    return {"spanA": span_a, "spanB": span_b, "trigger": trigger, "skeleton": skeleton,
            "construction": name, "relation": relation, "shape_fit": max(fit, 0), "note": note}


# --------------------------------------------------------------------------- #
#  FABULA — mint DiscourseEvent nodes + causes/before/coherence_rel edges from
#  the decode's own verdict (mechanical translation, not a new decision).
# --------------------------------------------------------------------------- #
def _mint_edge(sub, native, a, b, etype: str, attrs: Optional[dict] = None) -> None:
    if sub.has_edge(a, etype, b):
        return
    try:
        sub.add_edge(a, etype, b, attrs or {})
    except Exception:
        # admissibility-gated: `DiscourseEvent` is not (yet) in Γ's type
        # vocabulary, so the checked path always falls here for this node
        # type. `add_edge_unchecked` needs the ACTUAL NodeID objects (its
        # PyO3 signature takes `PyRef<PyNodeID>`, not a bare int) -- pass `a`
        # / `b` as-is, do NOT `_v()`-unwrap them here.
        try:
            native.add_edge_unchecked(a, etype, b, {**(attrs or {}), "gated": 0})
        except Exception:
            pass


def read_discourse(agent, text: str, *, window: int = 2, max_sentences: int = 40, unit=None) -> dict:
    """THE DRIVER. Segment `text` (the held sentence splitter,
    `reading_collapse._split_sentences`, reused as-is), mint one `DiscourseEvent`
    node per sentence, decode the coherence relation for every pair within
    `window` sentences of each other (adjacent pairs are the core RST case; a
    small window lets a satellite attach to a near-but-not-adjacent nucleus,
    which is also what gives the causal HINGE of a short narrative a higher
    degree than its neighbours — see the module docstring's centrality note),
    and mint the resulting `coherence_rel` (always) + `causes`/`before`
    (cause / sequence·condition) edges. Returns {text, sentences, nodes, pairs}."""
    ensure_codebook(agent)
    sub, native, _ = _resolve(agent)
    sentences = rc._split_sentences(text)[:max_sentences]
    # UNIT-SCOPED (MOVE 2b): each StoryUnit mints its OWN DiscourseEvent order
    # space (episode 2's order 0 is a distinct node from episode 1's order 0), so
    # the per-unit orders never collide. `unit=None` is the flat, pre-2b case.
    def _de_attrs(i, s):
        a = {"text": s, "order": i}
        if unit is not None:
            a["unit"] = unit
        return a
    nodes = [sub.add_node("DiscourseEvent", _de_attrs(i, s))
             for i, s in enumerate(sentences)]
    n = len(sentences)
    pairs: list = []
    for i in range(n):
        for j in range(i + 1, min(i + 1 + window, n)):
            rec = dict(coherence_between(agent, sentences[i], sentences[j]))
            rec["i"], rec["j"] = i, j
            rel = rec.get("relation")
            if rel is not None:
                _mint_edge(sub, native, nodes[i], nodes[j], "coherence_rel", {"relation": rel})
                if rel == "cause":
                    _mint_edge(sub, native, nodes[i], nodes[j], "causes")
                elif rel in ("sequence", "condition"):
                    _mint_edge(sub, native, nodes[i], nodes[j], "before")
            pairs.append(rec)
    return {"text": text, "sentences": sentences, "nodes": [_v(n) for n in nodes], "pairs": pairs}


# --------------------------------------------------------------------------- #
#  CENTRALITY — WEIGHTED node degree over the causes/enables/before/
#  coherence_rel graph, a graph Term (Times/Count/Neighbours/Plus), the
#  WINNER picked by Argmax (graph-native).
# --------------------------------------------------------------------------- #
def _degree_term(var_name: str = "x") -> dict:
    """degree(x) = sum over {causes,enables,before,coherence_rel} of
    weight(edge_type) * (Count(Neighbours(x,e)) + Count(InNeighbours(x,e))) --
    ONE Term-tree (`Plus` over `Times(Lit(weight), Count(...))`), the SAME
    `Count`/`Neighbours`/`InNeighbours`/`Times` idiom `gap_prioritiser.
    payoff_term` / `coref_entities._score_term` already compose. The WEIGHT is
    a `Lit` literal folded into the Term via `Times` -- the differential
    causal-vs-non-causal weighting is decided BY THE TERM (evaluated natively),
    not by Python arithmetic after the fact. No Python edge-walking."""
    v = {"type": "Var", "name": var_name}
    items = []
    for et in _FABULA_EDGE_TYPES:
        weight = {"type": "Lit", "value": _EDGE_WEIGHTS[et]}
        out_count = {"type": "Count", "source":
                     {"type": "Neighbours", "node": v, "edge_type": et, "any_type": False}}
        in_count = {"type": "Count", "source":
                    {"type": "InNeighbours", "node": v, "edge_type": et, "any_type": False}}
        items.append({"type": "Times", "items": [weight, out_count]})
        items.append({"type": "Times", "items": [weight, in_count]})
    return {"type": "Plus", "items": items}


def degree_of(agent, node) -> int:
    """One DiscourseEvent node's degree — a single Term evaluated with the node
    bound via env (no Python loop walks or counts edges; the loop over nodes in
    `centrality_ranking` below only DISPATCHES one Term per node)."""
    _, native, _ = _resolve(agent)
    val = native.evaluate(_degree_term("x"), {"x": node})
    return int(val) if isinstance(val, (int, float)) else 0


def _nodes_source(node_type: str, unit=None) -> dict:
    """`NodesOfType(node_type)`, UNIT-SCOPED (Wave 1A, mirrors the `unit` idiom
    situation_model_reader/discourse_coherence.read_discourse already use):
    when `unit` is given, wrap it in a `Filter` matching only nodes whose own
    `unit` attr equals it — so centrality never ranks a DIFFERENT flow's
    DiscourseEvent nodes in with this one's. `unit=None` is the byte-identical
    flat case (no Filter, exactly the prior Term)."""
    src = {"type": "NodesOfType", "node_type": node_type}
    if unit is None:
        return src
    return {"type": "Filter", "source": src, "var_name": "u",
            "predicate": {"type": "Eq",
                          "a": {"type": "Attr", "node": {"type": "Var", "name": "u"}, "key": "unit"},
                          "b": {"type": "Lit", "value": unit}}}


def most_central(agent, node_type: str = "DiscourseEvent", unit=None):
    """THE CENTRALITY DECISION: `Argmax` over `NodesOfType(node_type)` by
    `_degree_term` — the Trabasso & van den Broek causal-network centrality
    measure (most causal/coherence connections), read off ONE Term, never
    Python's `max()`/`sorted()`. Returns the winning node (native NodeID)."""
    _, native, _ = _resolve(agent)
    term = {"type": "Argmax", "source": _nodes_source(node_type, unit),
            "var_name": "x", "value": _degree_term("x"), "default": None}
    return native.evaluate(term)


def centrality_ranking(agent, node_type: str = "DiscourseEvent", unit=None) -> dict:
    """The full ranking, most-central first — the SUMMARY SUBSTRATE. The WINNER
    (`argmax_winner`) is independently decided by `most_central`'s `Argmax` Term
    (graph-native); the descending print ORDER for the rest is Python `sorted()`
    for DISPLAY ONLY — the same precedent `gap_prioritiser.rank_gaps` already
    establishes (Argmax decides; `sort()` displays) — verified below
    (`argmax_matches_top_of_sort`) to agree with the Argmax pick, so the sort
    never overrides the decision, it only presents it. UNIT-SCOPED (Wave 1A):
    `unit=None` is byte-identical to the prior flat behaviour; a given `unit`
    confines both the Argmax and the display ranking to that flow's own
    DiscourseEvent nodes (see `_nodes_source`)."""
    sub, _, _ = _resolve(agent)
    winner = most_central(agent, node_type, unit=unit)
    win_v = _v(winner) if winner is not None else None
    rows = [{"node": _v(n), "label": sub.node(n)["attrs"].get("text"), "degree": degree_of(agent, n)}
            for n in sub.nodes(node_type)
            if unit is None or sub.node(n)["attrs"].get("unit") == unit]
    rows.sort(key=lambda r: -r["degree"])   # DISPLAY-ONLY order; the decision was Argmax's.
    return {"ranking": rows, "argmax_winner": win_v,
            "argmax_matches_top_of_sort": bool(rows) and rows[0]["node"] == win_v}


__all__ = ["ensure_codebook", "coherence_between", "read_discourse",
           "degree_of", "most_central", "centrality_ranking"]

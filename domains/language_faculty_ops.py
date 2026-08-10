"""language_faculty_ops — the LANGUAGE-FACULTY leaf ops the composer chains.

The self-build composer (domains/reflective_faculty.py) authors GRAPH DATA from a
grounded concern. Until now it authored rule-chains, pipelines, and computational
Term primitives — but NOT a Program composing the agent's LANGUAGE faculties. The
prior consumption-quality fix had to implement its nominal-extraction filter as
ADAPTER LOGIC (domains/consumption_quality.is_nominal) because "the composer does
not yet author a POS-Program." This module EXPOSES the POS/nominal-head op as a
graph-resident, Program-callable LEAF so the composer can author the filter itself.

THE CLEAN SPLIT (mirrors domains/sense_selection_rules.py's sense decision):

  Boundary (Python, allowed): external I/O + mechanical MEASUREMENT only. The raw
    POS LOOKUP for a token — wiktionary_reference.wiktionary_pos +
    function_word_reference.classify — is a HELD-FACULTY CALL to an external lexical
    reference; no Term reads Wiktionary, so this is the honest leaf boundary. It
    measures a span's POS features and grounds them as Span node attrs (the same
    category as grounding SenseCandidate features).

  Leaf (graph-resident, THE DECISION): `nominal_head_term` — the nominal-vs-clause
    decision as a pure Term-tree over a span's measured POS-feature attrs
    (And-of-Nots over the drop conditions, in the Term algebra Eq/In/Not/And/Gt).
    It is Program-callable: it composes directly into a Filter, and the Rust
    evaluator runs it. This is the leaf the composer chains — the POS DECISION is
    a Term the agent authors; only the POS LOOKUP stays a held-faculty call.

  Filter (the composed Program, authored by the composer): `nominal_filter_program`
    — Filter(source=trig.has_span, var=span, predicate=nominal_head_term(span)).
    The composer (reflective_faculty._compose_language_faculty) assembles this from
    the grounded relations and installs it as a live Program node; this module only
    provides the Term constructors + the mechanical measurement + evaluation harness.

Equivalence: `nominal_head_term` reproduces consumption_quality.is_nominal's gates
exactly (a clause span fails, a nominal passes) — the SAME fragment-drop the adapter
is_nominal got, now COMPOSER-AUTHORED. is_nominal remains the per-span reference/
fallback leaf; the FILTER LOGIC is the authored Program.

DISCIPLINE (CLAUDE.md): no agent decision lives in Python here. The measurement is
mechanical POS reading; the DECISION is the Term the evaluator runs. The scratch
substrate the filter evaluates on is an implementation detail of the boundary (same
as sense_selection's), not the locus of the decision.
"""
from __future__ import annotations

import re
from typing import Any, Optional

# The seed carrying the language RelationCues + the 'filter' -> language_faculty
# ComposerCue. Loaded on demand (NOT in the minimal wall fixture) so the wall is
# reproducible; the composer + consumption_quality ensure it before grounding.
LANGUAGE_FACULTY_CUE_SEED = "language_faculty_cue"

# The named live Program the composer authors + installs.
NOMINAL_FILTER_PROGRAM = "nominal_filter"

# closed-class function labels a NOMINAL head never carries (a span whose HEAD is
# one of these is a clause / PP fragment). Same set consumption_quality.is_nominal
# reads off the function-word faculty.
_HEAD_BAD_FUNCTIONS = frozenset({"preposition", "conjunction", "determiner", "particle"})
_VERB_INFL = ("ing", "ed", "s")


# ---------------------------------------------------------------------------
# HELD-FACULTY CALL — the raw POS LOOKUP boundary (the honest leaf). No Term
# reads Wiktionary; this is external lexical I/O the world adapter performs.
# ---------------------------------------------------------------------------
def _tokens(surface: str) -> list[str]:
    """Split a (multi-word / hyphenated / underscored) surface into word tokens —
    mechanical surface op, no meaning."""
    return [t for t in re.split(r"[ _\-]+", str(surface).strip().lower()) if t]


def _pos(token: str, language: str = "en") -> list[str]:
    """The token's Wiktionary POS list (the held POS reference), primary-first.
    Empty on OOV (typically a technical noun). HELD-FACULTY CALL — external I/O."""
    from domains import wiktionary_reference as wr
    try:
        return wr.wiktionary_pos(token, language) or []
    except Exception:
        return []


def _function_of(token: str, language: str = "en") -> Optional[str]:
    """The token's coarse function-word label (determiner/preposition/...) via the
    closed-class faculty, or None for a content word. HELD-FACULTY CALL."""
    from domains import function_word_reference as fw
    try:
        return (fw.classify(token, language) or {}).get("function")
    except Exception:
        return None


def measure_span_features(surface: str, language: str = "en") -> dict:
    """MEASURE a span's POS features (the boundary): the head/lead POS + function
    label via the held POS faculty, reduced to the scalar/string attrs the
    graph-resident `nominal_head_term` reads. This is mechanical measurement — the
    DECISION over these features is the Term's, not this function's.

    Attrs (1.0/0.0 flags + POS-tag strings):
      empty        1.0 iff the surface has no word tokens
      head_bad_fn  1.0 iff the HEAD is a preposition/conjunction/determiner/particle
      hp0          the HEAD's primary POS tag ('' if OOV)
      hp_only_verb 1.0 iff the HEAD's POS list is exactly ['verb']
      lp0          the LEAD's primary POS tag ('' if OOV)
      lp_only_verb 1.0 iff the LEAD's POS list is exactly ['verb']
      lp_has_verb  1.0 iff 'verb' is among the LEAD's POS readings
      lead_infl    1.0 iff the LEAD is an inflected form (-ing/-ed/-s, len>3)
      multi        1.0 iff the span has more than one token
    """
    toks = _tokens(surface)
    if not toks:
        return {"empty": 1.0, "head_bad_fn": 0.0, "hp0": "", "hp_only_verb": 0.0,
                "lp0": "", "lp_only_verb": 0.0, "lp_has_verb": 0.0,
                "lead_infl": 0.0, "multi": 0.0}
    head, lead = toks[-1], toks[0]
    hp = _pos(head, language)
    lp = _pos(lead, language)
    return {
        "empty": 0.0,
        "head_bad_fn": 1.0 if _function_of(head, language) in _HEAD_BAD_FUNCTIONS else 0.0,
        "hp0": hp[0] if hp else "",
        "hp_only_verb": 1.0 if hp == ["verb"] else 0.0,
        "lp0": lp[0] if lp else "",
        "lp_only_verb": 1.0 if lp == ["verb"] else 0.0,
        "lp_has_verb": 1.0 if "verb" in lp else 0.0,
        "lead_infl": 1.0 if (lead.endswith(_VERB_INFL) and len(lead) > 3) else 0.0,
        "multi": 1.0 if len(toks) > 1 else 0.0,
    }


# ---------------------------------------------------------------------------
# TERM-JSON helpers — the same raw-dict Term form native_cognition / the composers
# build. Evaluated NATIVELY in Rust; no new primitive.
# ---------------------------------------------------------------------------
def _var(n: str) -> dict:
    return {"type": "Var", "name": n}


def _lit(v: Any) -> dict:
    return {"type": "Lit", "value": v}


def _attr(node: dict, key: str) -> dict:
    return {"type": "Attr", "node": node, "key": key}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


def _in(member: dict, container: dict) -> dict:
    return {"type": "In", "member": member, "container": container}


def _and(items: list) -> dict:
    return {"type": "And", "items": items}


def _not(arg: dict) -> dict:
    return {"type": "Not", "arg": arg}


def _flag(span_var: str, key: str) -> dict:
    """The graph-native truthiness of a 1.0/0.0 flag attr — Gt(attr+0, 0.5), the
    SAME shape self_verification._bool uses so a missing attr never errors."""
    return {"type": "Gt",
            "a": {"type": "Plus", "items": [_attr(_var(span_var), key), _lit(0)]},
            "b": _lit(0.5)}


# ---------------------------------------------------------------------------
# THE LANGUAGE LEAF — the nominal-vs-clause DECISION as a graph-resident Term.
# Reproduces consumption_quality.is_nominal's gates exactly, over the measured
# feature attrs. KEEP (nominal) iff NONE of the drop conditions holds.
# ---------------------------------------------------------------------------
def nominal_head_term(span_var: str = "span") -> dict:
    """The POS/nominal-head leaf: True iff the span bound to `span_var` is a NOMINAL
    (noun phrase), False iff it is a clause / verb-phrase / PP fragment. A pure
    Term-tree over the span's measured POS-feature attrs — the DECISION the composer
    chains, Program-callable, run by the Rust evaluator.

    The drop conditions (each a clause/fragment marker; is_nominal's gates):
      · empty span;
      · HEAD is a function word (preposition/conjunction/determiner/particle);
      · HEAD primary POS is 'adv';           · HEAD POS is exactly ['verb'];
      · LEAD primary POS in {adv, prep, conj};· LEAD POS is exactly ['verb'];
      · MULTI-word span LED by an inflected verb (-ing/-ed/-s + a verb reading);
      · MULTI-word span whose LEAD primary POS is 'verb'.
    """
    v = _var(span_var)
    drops = [
        _flag(span_var, "empty"),
        _flag(span_var, "head_bad_fn"),
        _eq(_attr(v, "hp0"), _lit("adv")),
        _flag(span_var, "hp_only_verb"),
        _in(_attr(v, "lp0"), _lit(["adv", "prep", "conj"])),
        _flag(span_var, "lp_only_verb"),
        _and([_flag(span_var, "multi"), _flag(span_var, "lp_has_verb"),
              _flag(span_var, "lead_infl")]),
        _and([_flag(span_var, "multi"), _eq(_attr(v, "lp0"), _lit("verb"))]),
    ]
    return _and([_not(d) for d in drops])


def nominal_filter_program(trig_var: str = "trig", span_var: str = "span") -> dict:
    """The composed FILTER Program: keep the nominal spans, drop the clause
    fragments. Filter(source=trig.has_span, var=span, predicate=nominal_head_term).
    Evaluating it over a batch of measured Span nodes returns the nominal ones.
    This is the Program the composer authors + installs; the predicate is the
    language leaf, the Filter/Neighbours are the held Term algebra it chains."""
    return {"type": "Filter",
            "source": {"type": "Neighbours", "node": _var(trig_var),
                       "edge_type": "has_span"},
            "var_name": span_var,
            "predicate": nominal_head_term(span_var)}


def keep_everything_program(trig_var: str = "trig", span_var: str = "span") -> dict:
    """The KNOWN-FAKE twin the #2 control must REJECT: the same Filter shape but a
    predicate that keeps EVERY span (Lit True). It agrees only on nominals, so every
    clause-fragment case FAILS it — a keep-everything filter has no teeth."""
    return {"type": "Filter",
            "source": {"type": "Neighbours", "node": _var(trig_var),
                       "edge_type": "has_span"},
            "var_name": span_var,
            "predicate": _lit(True)}


# ---------------------------------------------------------------------------
# EVALUATION HARNESS — ground measured Span nodes on a scratch substrate + run
# a filter Program (the composed leaf). World-adapter mechanics: it grounds the
# mechanically-measured features as graph nodes, evaluates the Program (the Rust
# evaluator decides), and reads the kept spans back. No Python decision.
# ---------------------------------------------------------------------------
def _fresh_substrate():
    """A fresh scratch substrate (no net, no agent state) to ground spans + run the
    Program on — the SAME boundary discipline sense_selection's scratch selector
    uses. The decision is the Program's; the substrate is an implementation detail."""
    from substrate_rs import _native
    s = _native.Substrate()
    try:
        s.add_production({
            "src": {"type": "SpanBatch", "var": "a"},
            "edge_type": "has_span",
            "tgt": {"type": "Span", "var": "b"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "language_faculty_ops",
        })
    except Exception:
        pass
    return s


def _add_edge(s, src, et, tgt) -> None:
    try:
        s.add_edge(src, et, tgt, {})
    except Exception:
        try:
            s.add_edge_unchecked(src, et, tgt)
        except Exception:
            pass


def run_filter_program(program_term: dict, surfaces: list[str],
                       language: str = "en") -> list[bool]:
    """Run a filter `program_term` over `surfaces` and return a parallel list of
    keep-flags (True == the Program kept this span). Grounds each surface as a
    measured Span node under one SpanBatch, evaluates the Program (the Rust
    evaluator runs the Filter), and reads which span ids survived. Mechanical."""
    if not surfaces:
        return []
    s = _fresh_substrate()
    trig = s.add_node("SpanBatch", {})
    ids: list = []
    for i, surface in enumerate(surfaces):
        feats = measure_span_features(surface, language)
        sp = s.add_node("Span", {**feats, "surface": str(surface), "idx": float(i)})
        _add_edge(s, trig, "has_span", sp)
        ids.append(sp)
    kept = s.evaluate(program_term, {"trig": trig})
    kept_set = set(kept or [])
    return [sp in kept_set for sp in ids]


def partition(program_term: dict, concepts: list, language: str = "en",
              *, surface_key=("surface", "name")) -> tuple[list, list]:
    """Partition `concepts` into (kept nominals, dropped fragments) by running the
    authored filter `program_term` over each concept's surface. The FILTER LOGIC is
    the Program's; this only reads each concept's surface + maps the verdict back."""
    def _surface(c):
        if isinstance(c, dict):
            for k in surface_key:
                if c.get(k):
                    return c[k]
            return ""
        return str(c)
    keeps = run_filter_program(program_term, [_surface(c) for c in concepts], language)
    kept, dropped = [], []
    for c, keep in zip(concepts, keeps):
        (kept if keep else dropped).append(c)
    return kept, dropped


# ===========================================================================
# THE SENSE-DISAMBIGUATOR LEAF + SELECT Program (the SECOND language leaf).
#
# The composer's language path is EXTENDED from a FILTER (keep nominal spans) to
# a SELECT (pick the sense that fits the context). The clean split mirrors the
# nominal leaf exactly:
#
#   HELD-FACULTY CALL (the honest leaf boundary): `sense_candidates` — the raw
#     WordNet SENSE ENUMERATION for a word + slot, with each candidate's measured
#     features (category / Lesk gloss overlap with the context / rank / freq).
#     External lexical I/O — no Term reads WordNet; this is the same measurement
#     dictionary_lexicon._enumerate_features performs (reused verbatim so the
#     candidate set + features are byte-identical to the adapter's pick_sense).
#
#   Leaf (graph-resident, THE SCORE): `sense_score_term` — a candidate's FIT to
#     the sentence context as a pure Term over the candidate's measured feature
#     attrs (100·[category fit] + 5·lesk_overlap + 1/(1+rank) + 0.001·freq). Reuses
#     sense_selection_rules.score_term so the number is the SAME graph Term the
#     boot-installed selection rule argmaxes — one source of truth, byte-identical.
#
#   SELECT (the composed Program, authored by the composer): `sense_select_program`
#     — Argmax(source=sel.has_candidate, var=cand, value=sense_score_term). The
#     composer (reflective_faculty._compose_language_faculty, sense branch) assembles
#     this and installs it as a live Program node; the ARGMAX-over-candidates-by-fit
#     is the DECISION the agent authors; only the WordNet ENUMERATION stays a call.
#
# Equivalence: run over the grounded candidates, the Argmax picks the SAME synset
# dictionary_lexicon.pick_sense picks (`water` -> the SUBSTANCE sense water.n.03 in
# "strip electrons from suitable substances such as water", not the Devon hamlet) —
# because it argmaxes the SAME score Term over the SAME candidate set.
# ===========================================================================

# The named live Program the composer authors + installs for the sense select.
SENSE_SELECT_PROGRAM = "sense_select"


def sense_candidates(head: str, slot: str, ctx: list, language: str = "en") -> list:
    """HELD-FACULTY CALL — the raw WordNet SENSE ENUMERATION for `head` under the
    POS the `slot` constrains, each candidate carrying its measured features
    (english_word / category / lesk_overlap-with-`ctx` / rank / freq / synset).
    External lexical I/O; no Term reads WordNet. Reuses dictionary_lexicon's own
    measurement so the candidate set is byte-identical to pick_sense's."""
    from domains import dictionary_lexicon as dl
    try:
        return dl._enumerate_features([head], slot, ctx, language) or []
    except Exception:
        return []


def sense_score_term(cand_var: str = "cand", sel_var: str = "sel") -> dict:
    """The sense-FIT SCORE leaf: a candidate sense's fit to the context as a pure
    Term over its measured feature attrs. Reuses sense_selection_rules.score_term
    (the SAME graph Term the boot selection rule argmaxes) so the composer-authored
    pick is byte-identical to the adapter's. This is the DECISION component the
    composer chains under the Argmax — the raw WordNet enumeration is the leaf call."""
    from domains import sense_selection_rules as ssr
    return ssr.score_term(cand_var, sel_var)


def sense_score_blind_term(cand_var: str = "cand", sel_var: str = "sel") -> dict:
    """The KNOWN-FAKE twin's score: identical to `sense_score_term` but with the
    CONTEXT term (Lesk gloss overlap) ZEROED — it scores category + rank + freq only,
    ignoring the sentence. It reproduces WordNet's context-blind default, so on a
    context-dependent case (mole=skin-vs-animal, cell=biology-vs-prison) it picks the
    WRONG sense and #2's control REJECTS it — a context-blind scorer has no teeth."""
    cand = _var(cand_var)
    sel = _var(sel_var)
    from domains import sense_selection_rules as ssr
    cat_hit = {"type": "IfThenElse",
               "cond": _in(_attr(cand, "category"), ssr._expected_categories_term(sel)),
               "then": _lit(1.0), "other": _lit(0.0)}
    rank_prior = {"type": "Div", "a": _lit(1.0),
                  "b": {"type": "Plus", "items": [_lit(1.0), _attr(cand, "rank")]}}
    return {"type": "Plus", "items": [
        {"type": "Times", "items": [_lit(ssr._W_CATEGORY), cat_hit]},
        # NOTE: the +5·lesk_overlap CONTEXT term is DROPPED — this is the blind fake.
        {"type": "Times", "items": [_lit(ssr._W_RANK), rank_prior]},
        {"type": "Times", "items": [_lit(ssr._W_FREQ), _attr(cand, "freq")]},
    ]}


def sense_select_program(sel_var: str = "sel", cand_var: str = "cand") -> dict:
    """The composed SELECT Program: Argmax over the selection's candidate senses of
    the sense-fit score Term. Argmax(source=sel.has_candidate, var=cand,
    value=sense_score_term). Evaluating it over the grounded SenseCandidate nodes
    returns the WINNING candidate node — the sense that best fits the context. This
    is the Program the composer authors + installs; the score is the language leaf,
    the Argmax/Neighbours are the held Term algebra it chains."""
    return {"type": "Argmax",
            "source": {"type": "Neighbours", "node": _var(sel_var),
                       "edge_type": "has_candidate"},
            "var_name": cand_var,
            "value": sense_score_term(cand_var, sel_var)}


def sense_select_blind_program(sel_var: str = "sel", cand_var: str = "cand") -> dict:
    """The KNOWN-FAKE twin the #2 control must REJECT: the same Argmax shape but the
    CONTEXT-BLIND score (no Lesk overlap). It agrees only where context is
    irrelevant, so a context-dependent case FAILS it."""
    return {"type": "Argmax",
            "source": {"type": "Neighbours", "node": _var(sel_var),
                       "edge_type": "has_candidate"},
            "var_name": cand_var,
            "value": sense_score_blind_term(cand_var, sel_var)}


def _fresh_sense_substrate():
    """A fresh scratch substrate carrying the slot->expected-category RolePriors the
    score Term reads (graph data from the seed) + the has_candidate production — the
    SAME boundary sense_selection_rules._ScratchSelector uses. The DECISION is the
    Program's Argmax; the substrate is an implementation detail of the boundary."""
    from substrate_rs import _native
    from domains import sense_selection_rules as ssr
    s = _native.Substrate()
    try:
        s.add_production({
            "src": {"type": "SenseSelection", "var": "a"},
            "edge_type": "has_candidate",
            "tgt": {"type": "SenseCandidate", "var": "b"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "language_faculty_ops",
        })
    except Exception:
        pass
    try:
        ssr._load_role_priors_from_seed(s)
    except Exception:
        pass
    return s


# PERSISTENT SENSE WORKSPACE — the expensive INVARIANT of the fresh-per-pick path
# (native Substrate + has_candidate production + role-prior seed load) built ONCE
# per process and REUSED across picks. The DECISION is unchanged: each pick still
# grounds its own SenseCandidate nodes under a FRESH SenseSelection and evaluates
# the SAME Argmax Program over that sel's has_candidate neighbours — so the winner
# is byte-identical. Only the substrate CREATE/teardown churn (~60% of the pick) is
# eliminated. Keyed by os.getpid() so a forked import worker LAZILY OWNS its own
# workspace on first post-fork use (never shares a parent's — parallel-safe).
_SENSE_WORKSPACE = None
_SENSE_WORKSPACE_PID = None


def _sense_workspace():
    """Lazy per-process singleton scratch substrate built EXACTLY as
    `_fresh_sense_substrate` builds it (production + RolePriors). Re-created if the
    pid changes (post-fork) so each worker owns its own — no cross-process sharing."""
    global _SENSE_WORKSPACE, _SENSE_WORKSPACE_PID
    import os
    pid = os.getpid()
    if _SENSE_WORKSPACE is None or _SENSE_WORKSPACE_PID != pid:
        _SENSE_WORKSPACE = _fresh_sense_substrate()
        _SENSE_WORKSPACE_PID = pid
    return _SENSE_WORKSPACE


def run_sense_select_program(program_term: dict, head: str, slot: str, ctx: list,
                             language: str = "en") -> Optional[dict]:
    """Run a sense-select `program_term` (the Argmax) over `head`'s candidate senses
    and return the winner as {sense, synset, rank, source} — byte-identical to
    dictionary_lexicon.pick_sense's winner (SAME candidate set, SAME score Term).
    Grounds each measured candidate as a SenseCandidate node under one SenseSelection,
    evaluates the Program (the Rust evaluator runs the Argmax), and reads the winning
    candidate's synset back. Returns None when WordNet has NO candidate (the OOV path
    the caller falls back on). Mechanical — the pick is the Program's.

    Uses the PERSISTENT per-process `_sense_workspace()` (production + RolePriors
    reused across picks) instead of building a fresh substrate every occurrence. Each
    pick still creates a FRESH SenseSelection + its own SenseCandidate nodes, so the
    Argmax's `sel.has_candidate` source sees ONLY this pick's candidates (no
    cross-pick leak); the per-pick nodes are removed after read-back so the workspace
    stays bounded. Same production, same role-prior, same Program → same winner."""
    feats = sense_candidates(head, slot, ctx, language)
    if not feats:
        return None
    s = _sense_workspace()
    sel = s.add_node("SenseSelection", {"slot": slot})
    scratch = [sel]
    by_id: dict = {}
    try:
        for c in feats:
            cn = s.add_node("SenseCandidate", {
                "english_word": c["english_word"], "category": c.get("category") or "?",
                "lesk_overlap": float(c.get("lesk_overlap", 0)), "rank": float(c.get("rank", 0)),
                "freq": float(c.get("freq", 0.0)), "sense": c.get("sense") or ""})
            scratch.append(cn)
            _add_edge(s, sel, "has_candidate", cn)
            by_id[cn] = c
        win = s.evaluate(program_term, {"sel": sel})
    finally:
        # Clear this pick's nodes COMPLETELY (remove_node drops incident edges too)
        # so no stale SenseCandidate leaks into the next pick's workspace.
        for nid in scratch:
            try:
                s.remove_node(nid)
            except Exception:
                pass
    if win is None or win not in by_id:
        return None
    c = by_id[win]
    syn = c.get("syn")
    return {"sense": syn.definition() if syn is not None else None,
            "synset": syn.name() if syn is not None else None,
            "rank": int(c.get("rank", 0)), "source": "wordnet+context"}


__all__ = [
    "LANGUAGE_FACULTY_CUE_SEED", "NOMINAL_FILTER_PROGRAM", "SENSE_SELECT_PROGRAM",
    "measure_span_features", "nominal_head_term", "nominal_filter_program",
    "keep_everything_program", "run_filter_program", "partition",
    "sense_candidates", "sense_score_term", "sense_score_blind_term",
    "sense_select_program", "sense_select_blind_program", "run_sense_select_program",
]

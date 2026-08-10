"""story_tree — A STORY'S NESTED STRUCTURE = COLLAPSE OVER A STORY-BOUNDARY
CODEBOOK, one level up from narrative_structure's per-sentence role collapse.

A real story is a TREE: episodes inside an arc, a tale inside a frame. The SAME
collapse that reads a clause's nested arguments (`reading_collapse.
_segment_into_clauses` / `read_clause_order_n`) and that reads a sentence's
story-grammar ROLE (`narrative_structure.recognize_narrative_structure`),
lifted ONE level up: a STORY is a residual that decodes into its StoryUnits at
recognised inter-sentence SEAMS.

  1. THE SEAM TOKEN. Each inter-sentence seam (between sentence i and i+1) is
     turned into a SINGLE-TOKEN skeleton by a MECHANICAL graph read off already-
     recognised faculties -- never a Python if/else naming the boundary, never a
     paragraph/blank-line/regex splitter:

       (a) TEMPORAL-SHIFT -- sentence_{i+1} LEADS with a temporal-shift episode
           marker ('some time later', 'one day', 'the next day', 'meanwhile',
           'later'), recognised by the SAME held-marker mechanism
           `discourse_coherence._leading_marker` uses (`reading_collapse.
           _marker_lexicon` over the held TEMPORAL_SHIFT MarkerClass forms), a
           leading single/multi-word n-gram match against graph data -> the
           token NARR is TEMPORAL_SHIFT;
       (b) EMBEDDED-NARRATIVE -- sentence_i carries a TELLING/speech marker
           (told/said/recounted), recognised off the held TELL MarkerClass: the
           reported sentences that follow are a nested tale -> EMBEDDED_NARRATIVE;
       (c) ARC-DISCONTINUITY -- the already-minted NarrativeRole arc
           (`narrative_structure`, reused, never re-derived) shows a resolution/
           consequence role at/before the seam then a fresh setup/problem role
           after it -> ARC_DISCONTINUITY (representation-bound: needs the upstream
           arc);
       else SEAM_NONE (no boundary signal).

  2. DECODE. That ONE token is decoded against a DEDICATED
     `ShapeSignatureStoryBoundary` codebook (`seeds/story_boundary.json`, its OWN
     codebook_type, kept separate from the clause-construction / coherence /
     narrative pools) by the SAME `ShapeDecode` shim `narrative_structure._decode`
     uses. The WINNING schema's own `boundary` attr is the verdict, read off via
     `reading_collapse._winner` (reused) -- the DECODE decides a boundary, not a
     Python `if`. SEAM_NONE covers no schema -> honest null -> NO boundary
     (precision-safe: a single-arc story stays ONE unit).

  3. MINT THE TREE. A root `StoryUnit` spans the whole story; each recognised
     boundary splits it into child `StoryUnit` nodes carrying their sentence
     span + the boundary signal that opened them, wired root -> child by
     `discourse_coherence._mint_edge` (reused verbatim -- the admissibility-gated
     write idiom the reading stack uses). The tree is minted into the graph and
     read back off for the gate.

ARCHITECTURE (CLAUDE.md). MOVE 2a is ADDITIVE RECOGNITION ONLY: it mints the
StoryUnit tree; it does NOT unit-scope the faculties or fire per-unit (that is
MOVE 2b) and it changes NO comprehension. The decision that carries content --
WHICH seam is a boundary -- is the `ShapeDecode` collapse's own verdict; this
module only (a) reads already-recognised marker/arc facts off held faculties
(mechanical), (b) builds the seam token (an existence check, not a boundary
assignment), (c) mints the resulting StoryUnit nodes/edges (mechanical graph
I/O). No `import re`; donkey = 0; no Python splitter deciding a boundary.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import discourse_coherence as dc
from domains import narrative_structure as ns
from domains import reading_collapse as rc

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "story_boundary.json")
_CODEBOOK_TYPE = "ShapeSignatureStoryBoundary"

# NarrativeRole role names that CLOSE a prior arc / OPEN a fresh one (read off
# the seed's own `role` attrs via the minted NarrativeRole nodes -- data, not a
# Python role-naming decision: these are the strings narrative_structure's OWN
# codebook already assigned, consulted here only as an existence check).
_CLOSING_ROLES = frozenset({"resolution", "consequence"})
_OPENING_ROLES = frozenset({"setup", "problem"})


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
    """Idempotently install the story-boundary codebook (the TEMPORAL_SHIFT /
    TELL MarkerClasses + the ShapeSignatureStoryBoundary nodes) plus its
    dependency (reading_constructions, for the marker-lexicon mechanism).
    Guarded by a graph-resident `Seed{id:'story_boundary'}` sentinel -- the SAME
    idempotency idiom narrative_structure.ensure_codebook uses. Mechanical seed
    I/O."""
    sub, _, _ = _resolve(agent)
    rc.ensure_codebook(agent)                 # reading_constructions (marker lexicon)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "story_boundary":
            return
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "story_boundary", "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  DECODE — a thin ShapeDecode shim pointed at the story-boundary codebook_type,
#  kept SEPARATE from the clause-construction / coherence / narrative pools
#  (mirrors narrative_structure._decode exactly).
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


def _boundary_for(agent, name: str) -> Optional[str]:
    sub, _, _ = _resolve(agent)
    for n in sub.nodes(_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get("boundary")
    return None


def decode_seam(agent, token: str) -> dict:
    """Decode ONE seam's token against the codebook. Returns {token,
    construction, boundary, shape_fit}. WHICH boundary (or none) is the decode's
    own verdict (`reading_collapse._winner`, reused) -- this only builds the
    one-element skeleton and reads the winner's `boundary` attr back. A token no
    schema covers (SEAM_NONE) -> boundary None (honest null, no seam split)."""
    ensure_codebook(agent)
    res = _decode(agent, [[token]])
    name, fit = rc._winner(res)
    boundary = _boundary_for(agent, name) if (name is not None and fit > 0) else None
    return {"token": token, "construction": name, "boundary": boundary,
            "shape_fit": max(fit, 0)}


# --------------------------------------------------------------------------- #
#  MECHANICAL SIGNALS — each an EXISTENCE check over already-recognised marker /
#  arc facts (the same shape narrative_structure._slot_token uses). These build
#  the TOKEN; they never assign a boundary.
# --------------------------------------------------------------------------- #
def _leading_temporal_shift(agent, sentence: str) -> Optional[str]:
    """The temporal-shift episode marker at the LEADING position of `sentence`,
    or None. Recognition against the held TEMPORAL_SHIFT MarkerClass forms
    (`reading_collapse._marker_lexicon`) -- a leading single/multi-word n-gram
    match, longest first, the SAME held-marker mechanism discourse_coherence.
    _leading_marker uses (no regex, no hardcoded phrase list; the phrases live in
    the seed's MarkerClass forms)."""
    sub, _, _ = _resolve(agent)
    words = ct._recognise_words(agent, sentence)
    if not words:
        return None
    lex = rc._marker_lexicon(sub)
    for k in (3, 2, 1):                       # longest leading n-gram wins
        if len(words) < k:
            continue
        phrase = " ".join(w.lower() for w in words[:k])
        if lex.get(phrase) == "TEMPORAL_SHIFT":
            return phrase
    return None


def _has_telling_marker(agent, sentence: str) -> Optional[str]:
    """The TELLING/speech marker (told/said/recounted/...) in `sentence`, or None
    -- recognised off the held TELL MarkerClass forms (recognition against graph
    data, not a verb list in Python). A sentence carrying one opens an embedded
    narrative at the following seam."""
    sub, _, _ = _resolve(agent)
    lex = rc._marker_lexicon(sub)
    for w in ct._recognise_words(agent, sentence):
        if lex.get(w.lower()) == "TELL":
            return w.lower()
    return None


def _arc_discontinuity(narrative_roles: list, i: int, j: int) -> bool:
    """Do the already-minted NarrativeRole nodes show a CLOSING role (resolution/
    consequence) at/before sentence i, then an OPENING role (setup/problem) at
    sentence j? An arc resolved, a fresh arc begun -- an episode seam read off
    narrative_structure's OWN committed arc (existence check, never re-derived).
    Empty when no arc has been minted (representation-bound)."""
    closing = any(r.get("order") is not None and int(r["order"]) <= i
                  and r.get("role") in _CLOSING_ROLES for r in narrative_roles)
    opening = any(r.get("order") is not None and int(r["order"]) >= j
                  and r.get("role") in _OPENING_ROLES for r in narrative_roles)
    return closing and opening


def _seam_token(agent, sentences: list, i: int, narrative_roles: list) -> tuple:
    """The token for ONE inter-sentence seam (between i and i+1), read off
    already-recognised facts. Mirrors narrative_structure._slot_token's own shape
    exactly (an existence-check ladder building a TOKEN, never the final
    boundary). Occam order: embedded (telling verb) -> temporal-shift (leading
    marker) -> arc-discontinuity (the minted arc) -> none."""
    j = i + 1
    tell = _has_telling_marker(agent, sentences[i])
    if tell is not None:
        return ("EMBEDDED_NARRATIVE",
                "sentence %d carries a telling/speech marker %r -- the following "
                "sentences are a reported (embedded) narrative" % (i, tell))
    ts = _leading_temporal_shift(agent, sentences[j])
    if ts is not None:
        return ("TEMPORAL_SHIFT",
                "sentence %d leads with the temporal-shift episode marker %r -- a "
                "jump forward in story time opening a new episode" % (j, ts))
    if _arc_discontinuity(narrative_roles, i, j):
        return ("ARC_DISCONTINUITY",
                "the minted NarrativeRole arc shows a resolution/consequence role "
                "at/before sentence %d then a fresh setup/problem role at/after "
                "sentence %d -- a prior arc resolved, a new arc begun" % (i, j))
    return ("SEAM_NONE",
            "sentence seam %d|%d carries no recognised boundary signal (no telling "
            "verb, no leading temporal-shift marker, no arc discontinuity)" % (i, j))


# --------------------------------------------------------------------------- #
#  MINT — a recognised boundary set becomes a root StoryUnit + child StoryUnits,
#  wired root -> child by discourse_coherence._mint_edge (reused verbatim).
# --------------------------------------------------------------------------- #
def _mint_unit(sub, attrs: dict):
    return sub.add_node("StoryUnit", dict(attrs))


def recognize_story_tree(agent, text: str, *, max_sentences: int = 60) -> dict:
    """Recognise a story's NESTED structure as a StoryUnit TREE by collapsing
    each inter-sentence seam against the story-boundary codebook. Mints a root
    StoryUnit spanning the whole story; each recognised boundary splits it into
    child StoryUnit nodes carrying their sentence span + the boundary signal that
    opened them. ADDITIVE RECOGNITION ONLY (MOVE 2a): the tree is minted; NO
    faculty is unit-scoped and NO comprehension changes (MOVE 2b).

    Returns {text, sentences, root, children, boundaries, seams, depth} -- a
    single-arc story with no recognised seam is a DEPTH-1 tree (root only,
    precision-safe)."""
    ensure_codebook(agent)
    sub, native, _ = _resolve(agent)
    sentences = rc._split_sentences(text)[:max_sentences]
    n = len(sentences)

    root = _mint_unit(sub, {"kind": "root", "span_start": 0,
                            "span_end": max(n - 1, 0), "n_sentences": n,
                            "role": "story"})
    out: dict[str, Any] = {"text": text, "sentences": sentences,
                           "root": {"node": _v(root), "span_start": 0,
                                    "span_end": max(n - 1, 0), "kind": "root",
                                    "n_sentences": n},
                           "children": [], "boundaries": [], "seams": [], "depth": 1}
    if n <= 1:
        return out

    # the already-minted arc (if any) -- reused, never re-derived. Empty on a bare
    # story_tree run over raw text (arc-discontinuity is representation-bound).
    narrative_roles = ns.read_narrative_roles(agent)

    boundaries: list = []
    for i in range(n - 1):
        token, note = _seam_token(agent, sentences, i, narrative_roles)
        dec = decode_seam(agent, token)
        seam = {"i": i, "j": i + 1, "token": token, "boundary": dec["boundary"],
                "shape_fit": dec["shape_fit"], "note": note}
        out["seams"].append(seam)
        if dec["boundary"] is not None:
            boundaries.append({"position": i + 1, "boundary": dec["boundary"],
                               "token": token, "note": note,
                               "construction": dec["construction"]})

    out["boundaries"] = boundaries
    if not boundaries:
        return out                            # DEPTH-1: single arc, precision-safe.

    # PARTITION the sentence span at the boundary positions into child StoryUnits
    # (siblings under root). Each child carries the boundary signal that OPENED
    # it (the first segment opens at the story start). A segment opened by an
    # embedded-narrative boundary is tagged kind='embedded'; else 'episode'.
    cuts = sorted(b["position"] for b in boundaries)
    bnd_at = {b["position"]: b for b in boundaries}
    starts = [0] + cuts
    ends = [c - 1 for c in cuts] + [n - 1]
    children: list = []
    for seg_i, (s0, s1) in enumerate(zip(starts, ends)):
        if s0 > s1:
            continue
        opener = bnd_at.get(s0)               # the boundary that opened this segment
        signal = opener["boundary"] if opener else "story_start"
        kind = "embedded" if signal == "embedded_narrative" else (
            "episode" if opener else "opening")
        cn = _mint_unit(sub, {"kind": kind, "span_start": s0, "span_end": s1,
                              "boundary_signal": signal,
                              "n_sentences": s1 - s0 + 1, "role": "story_unit",
                              "sentences": json.dumps(sentences[s0:s1 + 1])})
        dc._mint_edge(sub, native, root, cn, "has_story_unit", {"signal": signal})
        dc._mint_edge(sub, native, cn, root, "in_story", {})
        children.append({"node": _v(cn), "kind": kind, "span_start": s0,
                         "span_end": s1, "boundary_signal": signal,
                         "sentences": sentences[s0:s1 + 1],
                         "opened_by_note": opener["note"] if opener else
                         "the story's opening segment (no boundary before it)"})
    out["children"] = children
    out["depth"] = 2 if children else 1
    return out


# --------------------------------------------------------------------------- #
#  READ BACK — plain graph query (no decision), for callers/gates/demos.
# --------------------------------------------------------------------------- #
def read_story_tree(agent) -> dict:
    """Every resident StoryUnit node's attrs -- the root and its children, sorted
    by (span_start). A pure graph read for a caller to print or assert against."""
    sub, _, _ = _resolve(agent)
    root = None
    children = []
    for nd in sub.nodes("StoryUnit"):
        at = dict(sub.node(nd)["attrs"])
        at["node"] = _v(nd)
        if at.get("kind") == "root":
            root = at
        else:
            children.append(at)
    children.sort(key=lambda r: (r.get("span_start")
                                 if r.get("span_start") is not None else -1))
    return {"root": root, "children": children}


__all__ = ["ensure_codebook", "decode_seam", "recognize_story_tree",
           "read_story_tree"]

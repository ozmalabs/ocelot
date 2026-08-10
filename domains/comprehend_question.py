"""comprehend_question — THE COMPREHENSION FRONT: a RAW question text -> a formal
TARGET SPEC the elevator can ascend.

This is the FRONT DOOR the assistant used to be (plumbing-gap #1: it read the raw
HLE prose by hand and hand-crafted the formal target the elevator rode). Now the
AGENT reads the raw question with its OWN held machinery and produces the target:

    comprehend(question_text)
      1. READ      — the raw question text faithfully enters the graph (a Question
                     node; the world-adapter mints it). LaTeX is plainified to the
                     surface tokens the construction grammar reads (a mechanical
                     markup->text translation, the SAME kind read_and_ground's
                     _plainify_proofwiki is — no meaning decision).
      2. COMPREHEND — the agent's HELD construction grammar
                     (construction_grammar.apply_constructions) parses the question
                     SENTENCE into a relation FRAME {event, patient}: event = the
                     TARGET OPERATION asked for, patient = the OBJECT it ranges over.
                     The question constructions ('What is the <relation> of <owner>',
                     'Compute the <target> of <object>', 'Compute <target>') are
                     GRAPH DATA (seeds/constructions.json) — adding a question shape
                     is adding a construction, not code.
      3. MAP        — a thin TARGET-OP LEXICON (graph data: a relation-phrase ->
                     formal target op, an object-phrase -> the op's parameters) maps
                     the comprehended frame to the formal TargetSpec the elevator
                     ascends. The lexicon is the same surface->concept mapping the
                     constructions are; a relation-phrase / object-shape the lexicon
                     does NOT cover is the comprehension FRONTIER (honest None +
                     the reason — never a faked target).

A WORLD-ADAPTER (CLAUDE.md): it FETCHES the raw external text and SEQUENCES the
agent's own comprehension (the held construction grammar over graph-data
constructions + the held target-op lexicon over graph data). No `if` decides what
the question MEANS — the meaning is the construction frame; the target is the
lexicon lookup. No LLM. The honest boundary is the comprehension frontier: a
question whose shape the held constructions do not parse, or whose target/object
the lexicon does not map, returns a TargetSpec with grounded=False + the precise
gap, exactly as read_and_ground returns the un-comprehended case.

THE TARGET-OP LEXICON is graph data (seeds/question_targets.json): each entry is
{match: [phrase fragments that must all appear in the relation], op: the formal
target op the elevator ascends, params: {param -> object-fragment -> value}}. It is
the question-side analogue of the construction seeds — a named, extensible map from
the surface relation-phrase to the agent's held/acquirable target operation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from domains import construction_grammar as _cg

_SEED = Path(__file__).resolve().parent.parent / "seeds" / "question_targets.json"


# ---------------------------------------------------------------------------
# THE TARGET SPEC — the formal target the comprehension produces + the elevator
# ascends. `op` is the target op name (the elevator's ascend target); `params`
# are the object's parameters bound from the prose; `comprehended` carries the
# raw frame for the trace. grounded=False + reason = the comprehension frontier.
# ---------------------------------------------------------------------------

@dataclass
class TargetSpec:
    question_id: Optional[str] = None
    raw: str = ""
    grounded: bool = False               # did comprehension reach a formal target?
    # KIND — the question's TARGET kind. drive() does NOT route by this; it SEEDS
    # A GOAL, and the goal-pursuit machinery handles whatever the goal needs (the
    # right sub-action FALLS OUT of the pursuit). The kind only names the SHAPE of
    # the comprehended goal so the pursuit knows what it is pursuing:
    #   "world" — a COMPUTE goal (compute X): the pursuit RIDES the elevator.
    #   "know"  — a KNOW goal (what is X): the pursuit checks held -> not-held ->
    #             a REFERENCE wall -> the retrieval looks up wiki_local + grounds.
    #   "meta"  — a SELF goal (how do YOU retrieve / where is YOUR frontier): the
    #             pursuit reaches the agent's reflective faculty.
    #   "compound" — a COMPOUND goal ('what is X and compute Y'): it carries
    #             `subgoals` (child TargetSpecs of MIXED kinds); the pursuit
    #             DECOMPOSES it — seeds a child Goal per subgoal, pursues each
    #             recursively (each a leaf resolved by ITS faculty), composes.
    kind: str = "world"
    op: Optional[str] = None             # the formal target op (the ascend target)
    params: dict[str, Any] = field(default_factory=dict)
    # SUBGOALS (a COMPOUND goal): the child TargetSpecs the goal DECOMPOSES into.
    # When present, the goal is a COMPOUND/decompose node — the pursuit seeds a
    # child Goal per subgoal + pursues each recursively + composes; the leaf kinds
    # (world/know/meta) below name the resolution faculty. When empty, the goal is
    # a LEAF resolved directly by its kind's faculty. A subgoal IS a TargetSpec —
    # the goal/subgoal tree is the SAME structure, recursively.
    subgoals: list["TargetSpec"] = field(default_factory=list)
    relation_phrase: str = ""            # the comprehended target-operation phrase
    object_phrase: str = ""              # the comprehended object phrase
    comprehended: Optional[dict] = None  # the raw construction frame
    # KNOW field (kind == "know"): the CONCEPT the goal is to know (the comprehended
    # target of 'what is X' -> know(X)). The pursuit grounds it via the reference wall.
    know_concept: Optional[str] = None
    # META fields (kind == "meta"): the reflective TARGET + the faculty the driver
    # routes to + the captured meta-arg (e.g. the world op a needed-input is over).
    meta_target: Optional[str] = None    # retrieval_design / frontier / needed_input
    faculty: Optional[str] = None        # epistemic_access / order_n_postulates / ...
    meta_arg: Optional[str] = None       # the captured arg (e.g. 'X' in 'compute X')
    reason: str = ""

    def line(self) -> str:
        if not self.grounded:
            return (f"FRONTIER: {self.raw[:64]!r} -> "
                    f"relation={self.relation_phrase!r} object={self.object_phrase!r}"
                    f"  ({self.reason})")
        if self.kind == "compare":
            kids = " vs ".join(sg.know_concept or sg.op or "?"
                               for sg in self.subgoals if sg.kind != "contrast")
            return (f"{self.raw[:60]!r} -> [COMPARE] {kids} -> subgoals: "
                    f"know(X) + know(Y) + contrast")
        if self.kind == "contrast":
            return (f"{self.raw[:60]!r} -> [CONTRAST] over the grounded properties")
        if self.kind == "compound":
            kids = " + ".join(f"{sg.kind}({sg.op or sg.know_concept or sg.meta_target})"
                              for sg in self.subgoals)
            return (f"{self.raw[:60]!r} -> [COMPOUND] decompose into "
                    f"{len(self.subgoals)} subgoals: {kids}")
        if self.kind == "meta":
            arg = f"({self.meta_arg!r})" if self.meta_arg else ""
            return (f"{self.raw[:60]!r} -> [META] meta_target={self.meta_target}{arg}"
                    f"  -> faculty={self.faculty}")
        if self.kind == "know":
            return (f"{self.raw[:60]!r} -> [KNOW] goal=know({self.know_concept!r})")
        ps = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        return (f"{self.raw[:60]!r} -> [WORLD] target={self.op}({ps})  "
                f"[relation {self.relation_phrase!r} | object {self.object_phrase!r}]")


# ---------------------------------------------------------------------------
# READ — plainify the LaTeX/markup question text into the surface tokens the
# held construction grammar reads. A MECHANICAL markup->text translation (the
# same kind as read_and_ground._plainify_proofwiki) — NOT a meaning decision.
# ---------------------------------------------------------------------------

def plainify(text: str) -> str:
    """Plainify a raw HLE question's LaTeX into readable surface tokens. Drops the
    $...$ math delimiters keeping the inner symbols, maps the common math macros to
    their readable names (\\mathbb{Q} -> Q, \\sqrt -> sqrt), and flattens braces.
    Mechanical world-adapter surface op — the construction grammar then reads the
    plain tokens. No meaning decided here."""
    t = text or ""
    # unwrap inline math $...$ keeping the inner content.
    t = re.sub(r"\$([^$]*)\$", r"\1", t)
    # common macros -> readable names (the surface the grammar/lexicon read).
    for macro, repl in (
            ("\\mathbb", ""), ("\\mathcal", ""), ("\\mathfrak", ""),
            ("\\sqrt", "sqrt"), ("\\times", "x"), ("\\ast", "*"),
            ("\\to", "to"), ("\\cap", "cap"), ("\\infty", "infinity"),
            ("\\left", ""), ("\\right", ""), ("\\,", " ")):
        t = t.replace(macro, repl)
    t = t.replace("{", "(").replace("}", ")")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.])\s+", text or "") if s.strip()]


# ---------------------------------------------------------------------------
# THE TARGET-OP LEXICON — graph data mapping the comprehended relation-phrase ->
# the formal target op + the object-phrase -> the op's params. Read from
# seeds/question_targets.json; the in-module mirror is the fallback so the front
# works in a bare world adapter too (the SAME pattern as load_definition_structure).
# ---------------------------------------------------------------------------

_LEXICON_FALLBACK: list[dict] = [
    {"op": "largest_noncyclic_torsion_order",
     "match": ["largest", "order"],
     "object_must": ["torsion", "elliptic"],
     "params": {"field": [
         {"object_has": ["sqrt", "3"], "value": "Q(sqrt(-3))"}]}},
    {"op": "reduced_spin_bordism",
     "match": ["spin", "bordism"],
     "object_must": ["classifying", "g2"],
     "degree_from_relation": True,
     "params": {"space": [
         {"object_has": ["g2"], "value": "BG2"}]}},
    {"op": "first_homology",
     "match": ["h", "1"],
     "params": {"space": [
         {"object_has": ["lattice"], "value": "moduli_lattices_unit_area"},
         {"object_has": ["x"], "value": "X"}]}},
]


def load_lexicon(path: Path = _SEED) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text())
        lex = data.get("targets")
        if isinstance(lex, list) and lex:
            return lex
    except Exception:
        pass
    return _LEXICON_FALLBACK


# ---------------------------------------------------------------------------
# THE META-TARGET LEXICON — graph data mapping a SELF/META question's surface
# fragments -> the reflective META-TARGET + the FACULTY the driver routes to.
# The question-side analogue of the world target-op lexicon (above), but for a
# question ABOUT THE AGENT ITSELF. Read from seeds/question_targets.json; the
# in-module mirror is the fallback (same pattern as _LEXICON_FALLBACK).
# ---------------------------------------------------------------------------

# A SELF-REFERENCE cue — a meta question is ABOUT THE AGENT, so it carries a
# 'you'/'your'/'yourself'/'me' self-reference. A world/math question ('compute
# the X of Y') does not; this keeps a meta-target from firing on a world
# question.
_SELF_CUES = {"you", "your", "yourself", "yours", "me"}

_META_LEXICON_FALLBACK: list[dict] = [
    {"meta_target": "retrieval_design", "faculty": "epistemic_access",
     "match": ["retrieve"], "any": [["how"], ["want"]]},
    {"meta_target": "retrieval_design", "faculty": "epistemic_access",
     "match": ["how", "get", "information"]},
    {"meta_target": "frontier", "faculty": "order_n_postulates",
     "match": ["frontier"]},
    {"meta_target": "frontier", "faculty": "order_n_postulates",
     "match": ["where", "stuck"]},
    {"meta_target": "needed_input", "faculty": "diagnose_wall",
     "match": ["need"], "arg_after": ["to", "compute"]},
    {"meta_target": "needed_input", "faculty": "diagnose_wall",
     "match": ["need", "compute"], "arg_after": ["compute"]},
]


# SELF-MODEL meta-targets (domains/self_model.py's query handlers) — appended
# in-code rather than added to seeds/question_targets.json: that file is a
# graph-DATA seed outside this task's editable-file set, and (unlike the
# world-target lexicon) `load_meta_lexicon` only falls back to a Python list
# when the seed is EMPTY, which it isn't (55 entries) — so a fallback-only
# addition would never be reached. Appending here (always, whichever source
# supplied the base list) is the smallest change that lands the three new
# question shapes without touching the seed file.
#
# 'what does <rule> do' carries no you/your/me self-cue on its own (it names
# a rule, not the agent) — `self_cue_optional` lets THIS entry bypass the
# self-cue gate (see `comprehend_meta`); a nonsense/unheld name still comes
# back honest (`self_model.run_self_model_rule`'s exact-match lookup), so a
# world question that happens to share the 'what does X do' shape is a safe,
# discriminative miss, not a wrong answer.
_SELF_MODEL_META_ENTRIES: list[dict] = [
    {"meta_target": "self_model_rule", "faculty": "self_model",
     "match": ["what", "does", "do"], "self_cue_optional": True,
     "arg_between": {"start": ["does"], "end": ["do"]}},
    {"meta_target": "self_model_topic", "faculty": "self_model",
     "match": ["which", "rules", "about"], "arg_after": ["about"]},
    {"meta_target": "self_model_touches", "faculty": "self_model",
     "match": ["which", "parts", "touch"], "arg_after": ["touch"]},
]


def load_meta_lexicon(path: Path = _SEED) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text())
        lex = data.get("meta_targets")
        if isinstance(lex, list) and lex:
            return list(lex) + _SELF_MODEL_META_ENTRIES
    except Exception:
        pass
    return _META_LEXICON_FALLBACK + _SELF_MODEL_META_ENTRIES


def _has_self_cue(tokens: list[str]) -> bool:
    """Does the question carry a SELF-REFERENCE ('you'/'your')? The precondition
    for a meta question — it must be ABOUT the agent. A surface read, not a
    meaning decision."""
    return any(t in _SELF_CUES for t in tokens)


def _arg_after(tokens: list[str], anchor: list[str]) -> Optional[str]:
    """Capture the meta-ARG: the phrase that FOLLOWS the `anchor` fragments in
    the token stream (e.g. the tail after 'compute' in 'what do you need to
    compute the spin bordism of bg2' -> 'the spin bordism of bg2'). A surface
    slice, not a meaning decision. Returns None when the anchor is not found or
    nothing follows it."""
    anchor = [_norm(a) for a in anchor]
    n = len(anchor)
    for i in range(len(tokens) - n + 1):
        if tokens[i:i + n] == anchor:
            tail = tokens[i + n:]
            if tail:
                return " ".join(tail)
    return None


def _arg_between(tokens: list[str], start: list[str], end: list[str]) -> Optional[str]:
    """Capture the meta-ARG BOUNDED BETWEEN two anchors (e.g. the 'X' in 'what
    does X do' — the span after the LAST `start` match up to the FIRST `end`
    match found after it). Generalises `_arg_after` to a closed span, for
    shapes where the tail has a known trailing word (like the shape's own 'do')
    that must NOT be captured as part of the argument. A surface slice, not a
    meaning decision; returns None when either anchor is missing or the span
    between them is empty."""
    start = [_norm(a) for a in start]
    end = [_norm(a) for a in end]
    ns, ne = len(start), len(end)
    start_end_idx = None
    for i in range(len(tokens) - ns + 1):
        if tokens[i:i + ns] == start:
            start_end_idx = i + ns   # last occurrence wins
    if start_end_idx is None:
        return None
    for j in range(start_end_idx, len(tokens) - ne + 1):
        if tokens[j:j + ne] == end:
            span = tokens[start_end_idx:j]
            return " ".join(span) if span else None
    return None


def comprehend_meta(question_text: str,
                    meta_lexicon: Optional[list[dict]] = None
                    ) -> Optional[dict]:
    """Recognize a SELF/META question + parse its META-TARGET. A meta question is
    ABOUT THE AGENT (carries a 'you'/'your'/'me' self-cue) and matches a
    meta-target entry's surface fragments. Returns {meta_target, faculty,
    meta_arg} when a meta-target fires, or None (NOT a meta question -> the
    world parse runs). A pure data lookup over the meta lexicon — no decision
    about meaning.

    Each entry fires iff: (the question carries a self-cue, OR the entry
    declares `self_cue_optional` — a shape unambiguous enough to not need one,
    e.g. 'what does <rule> do' names a specific held mechanism rather than the
    agent generically; see `comprehend_question._SELF_MODEL_META_ENTRIES`),
    ALL `match` fragments appear, AND for every group in `any` (optional) at
    least one fragment appears. `arg_after` (optional) captures the tail after
    the anchor as the meta-arg; `arg_between` (optional) captures the BOUNDED
    span between two anchors instead."""
    lex = meta_lexicon or load_meta_lexicon()
    toks = _tokens(question_text)
    tokset = set(toks)
    has_cue = _has_self_cue(toks)
    for entry in lex:
        if not has_cue and not entry.get("self_cue_optional"):
            continue
        if not _all_present(entry.get("match", []), tokset):
            continue
        anys = entry.get("any") or []
        if anys and not all(any(_norm(a) in tokset for a in grp) for grp in anys):
            continue
        meta_arg = None
        anchor = entry.get("arg_after")
        if anchor:
            meta_arg = _arg_after(toks, anchor)
        between = entry.get("arg_between")
        if between:
            meta_arg = _arg_between(toks, between.get("start") or [], between.get("end") or [])
        # a design route may carry the WHOLE question as the goal description (the
        # goal's target shape is authored from it downstream) — data-driven, not a
        # decision about meaning.
        if entry.get("goal_from_question"):
            meta_arg = question_text
        return {"meta_target": entry["meta_target"],
                "faculty": entry["faculty"], "meta_arg": meta_arg}
    return None


# A KNOW question is a bare DEFINITIONAL ask: 'what is X' / 'what are X' / 'what
# is a/an X' / 'what does X mean' — it seeds the goal 'know X' (the agent does
# not route it anywhere; the pursuit grounds X via the reference wall). The
# leading 'what is/are' frame + the bare concept tail; NOT a world target-op ('the
# largest order of ...') and NOT a self/meta question (no 'you'/'your' self-cue).
_KNOW_LEAD = re.compile(
    r"^\s*what\s+(?:is|are)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s*\??\s*$",
    re.IGNORECASE)
_KNOW_MEAN = re.compile(
    r"^\s*what\s+does\s+(.+?)\s+mean\s*\??\s*$", re.IGNORECASE)
# Composition/material ask: "what is the moon made of?" — the SUBJECT is the
# topic (moon), not the tail phrase "moon made of". Excluded from comprehend_know
# so the frame parser + topic-route path can handle it.
_MADE_OF = re.compile(
    r"^\s*what\s+(?:is|are)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+made\s+of\s*\??\s*$",
    re.IGNORECASE)


def comprehend_composition(question_text: str) -> Optional[str]:
    """Recognize a material/composition question ('what is X made of?') and
    return the SUBJECT nominal X, or None. A surface read of the leading frame,
    NOT a meaning decision — the pursuit routes X to answer_topic grounding."""
    text = (question_text or "").strip()
    m = _MADE_OF.match(text)
    if m is None:
        return None
    subject = m.group(1).strip().rstrip("?.").strip()
    return subject or None


def comprehend_know(question_text: str,
                    lexicon: Optional[list[dict]] = None) -> Optional[str]:
    """Recognize a bare KNOW question ('what is X') + return the CONCEPT to know,
    or None (not a know question). The goal 'know X' is seeded from the concept
    tail; the pursuit grounds X via the reference wall (wiki_local). A surface
    read, NOT a meaning decision — the concept is the noun phrase the 'what is'
    frame ranges over.

    Guarded so it does NOT swallow a world target-op question: a 'what is X' whose
    X the world target-op lexicon maps ('what is the largest order of a torsion
    subgroup ...') is a COMPUTE goal, not a bare KNOW goal — that is handled by the
    world parse, so here we only fire when the tail does NOT map to a world op.
    A self/meta question ('what do you need ...') is excluded by the self-cue check
    its caller already ran (comprehend runs comprehend_meta first)."""
    text = (question_text or "").strip()
    # A composition ask is NOT a bare know('X made of') goal — let the frame
    # parser + topic-route path handle it (subject = X, aspect = made_of).
    if _MADE_OF.match(text) is not None:
        return None
    m = _KNOW_LEAD.match(text) or _KNOW_MEAN.match(text)
    if m is None:
        return None
    concept = m.group(1).strip().rstrip("?.").strip()
    if not concept:
        return None
    # do NOT swallow a world target-op question: if the tail maps to a world op,
    # let the world parse handle it (a COMPUTE goal, not a bare KNOW goal).
    lex = lexicon or load_lexicon()
    rel_obj = plainify(text)
    if _map_to_target(rel_obj, rel_obj, lex) is not None:
        return None
    return concept


# ---------------------------------------------------------------------------
# THE COMPOUND RECOGNIZER — a COMPOUND question ('what is X and compute Y')
# DECOMPOSES into SUBGOALS. A surface SPLIT on a top-level ' and ' connective
# into clauses, each recursively comprehended into a subgoal TargetSpec; the
# compound fires iff >= 2 clauses each comprehend to a grounded LEAF (so a flat
# 'what is X and Y' noun-phrase — one know-leaf — is NOT mis-split). The pursuit
# decomposes the compound; each subgoal is resolved by ITS leaf faculty. A surface
# read (the connective), NOT a meaning decision — the meaning is each subgoal's.
# ---------------------------------------------------------------------------

# the clause connectives a compound question joins its sub-questions with. A
# surface token, the question-side analogue of the construction connectives —
# splitting on it yields the candidate sub-question clauses (each re-comprehended).
_COMPOUND_SPLIT = re.compile(r"\s+and\s+(?:then\s+)?", re.IGNORECASE)


def comprehend_compound(question_text: str, *,
                        constructions: Optional[list[dict]] = None,
                        lexicon: Optional[list[dict]] = None,
                        _comprehend=None) -> Optional[list["TargetSpec"]]:
    """Recognize a COMPOUND question + return its SUBGOAL TargetSpecs, or None (not
    compound). A compound question joins >= 2 sub-questions with a clause connective
    ('what is X and compute Y'); each clause is recursively comprehended into a LEAF
    subgoal of its own kind (a KNOW subgoal + a COMPUTE subgoal -> MIXED faculties).

    The split is a SURFACE read on the connective; the meaning of each subgoal is
    that subgoal's OWN comprehension (the same front, recursively). Fires only when
    the split yields >= 2 clauses that EACH comprehend to a grounded leaf — a flat
    question with an incidental 'and' (a single noun phrase, or one clause that does
    not ground) is NOT a compound goal, so the flat parse keeps priority. A surface
    decision, not a meaning decision; never a faked decomposition.

    DEPTH > 1 (the goal/subgoal TREE): with >= 3 clauses ('A and B and C'), the
    decomposition NESTS — the FIRST clause is a leaf subgoal + the TAIL ('B and C')
    re-comprehends into a SUB-COMPOUND subgoal (which itself decomposes). So the
    tree grows depth-2+ ([A, compound[B, C]]) — a subgoal seeds sub-subgoals, the
    SAME decompose-or-resolve recursively. A 2-clause compound stays depth-1."""
    text = (question_text or "").strip()
    parts = [p.strip().rstrip(".?!") for p in _COMPOUND_SPLIT.split(text)]
    parts = [p for p in parts if p]
    if len(parts) < 2:
        return None
    comp = _comprehend or comprehend

    # DEPTH > 1: with >= 3 clauses, NEST the tail into a sub-compound so the goal
    # tree grows depth-2+ (the head is a leaf subgoal; the tail re-comprehends into
    # a compound subgoal that decomposes further). The SAME structure, recursively.
    if len(parts) >= 3:
        head = comp(parts[0], constructions=constructions, lexicon=lexicon)
        tail_text = " and ".join(parts[1:])
        tail = comp(tail_text, constructions=constructions, lexicon=lexicon)
        if (head.grounded and head.kind != "compound"
                and tail.grounded and tail.kind == "compound"):
            return [head, tail]
        # fall through to the flat parse if the nesting did not ground cleanly.

    subgoals: list[TargetSpec] = []
    for clause in parts:
        # each clause is a self-contained sub-question; re-comprehend it through
        # the SAME front (recursively). A leaf subgoal is grounded + NOT itself
        # compound (a single ' and ' nesting level — the demo's depth).
        sub = comp(clause, constructions=constructions, lexicon=lexicon)
        if not sub.grounded or sub.kind == "compound":
            return None
        subgoals.append(sub)
    # genuinely compound: >= 2 grounded leaves of (possibly) MIXED kinds.
    return subgoals if len(subgoals) >= 2 else None


# ---------------------------------------------------------------------------
# THE COMPARISON CONSTRUCTION — the question-side ACQUIRE-CONSTRUCTION (cmsg81 at
# the GOAL level). A 'compare X with/and Y' question is an UNRECOGNIZED GOAL-SHAPE
# the held question constructions do NOT cover (the cmsg108 frontier — drive()
# returns grounded=False, an honest WALL). The metacognitive loop crosses it:
#
#   1. ASK WHY (diagnose the gap)   — diagnose_comprehension_gap names the missing
#      construction: the head verb 'compare' + the 'with'/'and' connective is the
#      unrecognized goal-shape; the agent LACKS the 'compare ... with ...'
#      construction (a COMPARISON goal-type). The same way the climbing-spike
#      diagnoses a wall-KIND — the agent names WHY it did not understand.
#   2. SEEK TO UNDERSTAND (acquire) — acquire_compare_construction ACQUIRES the
#      construction: read/abstract -> the comparison goal-DECOMPOSITION know(X) +
#      know(Y) + contrast(X,Y). Added as GRAPH DATA here (_ACQUIRED_QUESTION,
#      the question-side analogue of construction_grammar._ACQUIRED_DEFN). The
#      'compare X with Y' compound is KIN to the cmsg108 'X and Y' compound; the
#      contrast over the two grounded properties is the ADDED structure.
#   3. RE-COMPREHEND -> PURSUE     — comprehend now recognizes the comparison goal
#      (comprehend_compare fires off the ACQUIRED construction) -> the subgoal tree
#      [know(X) -> wiki_local, know(Y) -> wiki_local, contrast] -> pursued.
#
# Faithful (CLAUDE.md): the construction is GRAPH DATA (acquired markers), not code;
# the recognizer reads the held/acquired data; the diagnosis + acquire mirror the
# agent's own acquire_construction (read-how-to-read / abstract-from-the-kin-
# construction). No LLM. The honest limit: which frontiers the agent can cross by
# read/abstract (the compare shape, KIN to a held compound) vs the genuinely-novel
# (articulable but not yet acquirable).
# ---------------------------------------------------------------------------

# the ACQUIRED question-side constructions — graph data the agent MINTS when it
# crosses a comprehension frontier by acquiring the construction. EMPTY until
# acquired: a 'compare X with Y' question FRONTIERS (grounded=False) until the
# metacognitive loop acquires the construction (the demo shows the before->after).
_ACQUIRED_QUESTION: dict = {
    # each entry: {kind, head, connectives, decompose} — `head` is the head verb
    # that opens the goal-shape ('compare'); `connectives` are the surface joiners
    # the two operands sit across ('with'/'and'); `decompose` names the goal's
    # subgoal-shape (know(X) + know(Y) + contrast). Read by comprehend_compare.
    "comparison": [],
}

# the comparison construction the agent ACQUIRES (the held shape minted on acquire).
# Kept as the canonical form acquire_compare_construction installs — it is the
# question-side analogue of _DEFN_OPENER_VOCAB / _DEFN_CONDITION_VOCAB: the small
# closed surface family of a comparison goal-shape.
_COMPARE_HEAD_VOCAB = ["compare", "contrast"]
_COMPARE_CONNECTIVE_VOCAB = ["with", "and", "to", "versus", "vs"]

# the head-verb-led comparison surface ('compare X with Y' / 'contrast X and Y').
# The recognizer reads this OFF the acquired construction's markers (not hardcoded
# behaviour): the head verb leads, a connective splits the two operands.
_COMPARE_LEAD = re.compile(r"^\s*(\w+)\s+(.+)$", re.IGNORECASE)

# the COMPARISON MEANING the agent HOLDS (the cmsg109 construction). A construction
# is ONE meaning realized by MANY surfaces — this is the meaning; the head-led form
# ('compare X with Y') and any acquired SURFACE TEMPLATE ('how does X differ from Y')
# are all SURFACES OF IT, decomposing to the SAME subgoal-shape. The meaning-vs-
# surface distinction the meta-meta loop reaches (the prosody Mt's function-vs-
# realization, at the goal level: a comparison FUNCTION, many SERIALIZATIONS).
_COMPARISON_MEANING = ["know(X)", "know(Y)", "contrast(X,Y)"]

# additional SURFACE TEMPLATES for the held comparison meaning the agent ACQUIRES
# when the meta-meta loop crosses a surface it did not recognize. Each template is a
# marker-pattern with {x}/{y} slots ('how does {x} differ from {y}') — a SURFACE of
# the SAME held comparison meaning, NOT a new meaning. EMPTY until the surface-
# variation acquire mints it (the demo shows the before->after on 'differ from').
_COMPARE_SURFACE_VOCAB = [
    "how does {x} differ from {y}",
    "the difference between {x} and {y}",
    "what is the difference between {x} and {y}",
    "how do {x} and {y} differ",
]


def _match_surface_template(template: str, text: str) -> Optional[tuple[str, str]]:
    """Match an acquired SURFACE TEMPLATE ('how does {x} differ from {y}') against the
    question text, returning the (x, y) operand surfaces or None. A pure surface read
    over the template's literal markers + {x}/{y} slots — the question-side analogue
    of construction_grammar's slot-fill. NOT a meaning decision: the meaning is the
    HELD comparison; this only recognizes a SURFACE that realizes it."""
    pat = re.escape(template)
    pat = pat.replace(r"\{x\}", r"(?P<x>.+?)").replace(r"\{y\}", r"(?P<y>.+?)")
    m = re.match(r"^\s*" + pat + r"\s*\??\s*$", _norm(text))
    if m is None:
        return None
    x = (m.group("x") or "").strip()
    y = (m.group("y") or "").strip()
    return (x, y) if (x and y) else None


def diagnose_comprehension_gap(question_text: str) -> Optional[dict]:
    """ASK WHY — diagnose WHY the comprehension failed: WHICH construction is
    missing. For 'compare HTTP with FTP': the head verb 'compare' + a 'with'/'and'
    connective is an UNRECOGNIZED GOAL-SHAPE the held question constructions do not
    parse — the agent LACKS the 'compare ... with ...' construction (a COMPARISON
    goal-type). Returns the named gap {missing_construction, head, connective,
    operands, why} or None (no recognizable construction-shape to name — a
    genuinely-novel frontier the agent can wall on but not yet articulate).

    A surface read of the head + connective (the same kind of structural diagnosis
    as the climbing-spike's wall-KIND), NOT a meaning decision. The agent NAMES
    what it does not understand — the metacognition the user has pushed for."""
    toks = _tokens(question_text)
    if not toks:
        return None
    head = toks[0]
    if head not in _COMPARE_HEAD_VOCAB:
        return None  # not a comparison-shaped frontier — cannot name this gap.
    # find the connective splitting the two operands.
    conn = next((c for c in _COMPARE_CONNECTIVE_VOCAB if c in toks[1:]), None)
    if conn is None:
        return None
    ci = toks.index(conn, 1)
    x = " ".join(toks[1:ci]).strip()
    y = " ".join(toks[ci + 1:]).strip()
    if not (x and y):
        return None
    return {
        "missing_construction": f"{head} {{X}} {conn} {{Y}}",
        "construction_kind": "comparison",
        "head": head, "connective": conn,
        "operands": [x, y],
        "why": (f"the head verb {head!r} + the {conn!r} connective is an "
                f"UNRECOGNIZED GOAL-SHAPE; the held question constructions cover "
                f"'what is X', 'compute X', 'X and Y' (compound) — but NOT a "
                f"COMPARISON ('{head} X {conn} Y'). The agent lacks the comparison "
                f"construction."),
    }


def acquire_compare_construction(gap: dict) -> dict:
    """SEEK TO UNDERSTAND — ACQUIRE the comparison construction named by the gap
    (the cmsg81 acquire-construction, at the GOAL level). The agent acquires it by
    ABSTRACTING from its held kin (the cmsg108 'X and Y' COMPOUND is the kin; a
    'compare X with Y' ADDS a CONTRAST over the two grounded properties) — the
    comparison goal-DECOMPOSITION is know(X) + know(Y) + contrast(X,Y). Mints the
    construction as GRAPH DATA (_ACQUIRED_QUESTION) so comprehend_compare recognizes
    it. Returns {acquired, construction, before, after}: `before`/`after` is whether
    the gap's example comprehends BEFORE/AFTER the acquire (the proof the frontier
    was crossed). Faithful: the markers are read/abstracted, held as data; no LLM."""
    example = f"{gap['head']} {gap['operands'][0]} {gap['connective']} {gap['operands'][1]}"
    before = comprehend(example).grounded
    construction = {
        "kind": "comparison",
        "head": gap["head"],
        "connectives": list(dict.fromkeys([gap["connective"]]
                                          + _COMPARE_CONNECTIVE_VOCAB)),
        # the goal-DECOMPOSITION: a comparison goal -> know(X) + know(Y) +
        # contrast(X,Y). The contrast = compare the two grounded properties (the
        # ADDED structure over the kin compound 'X and Y').
        "decompose": ["know(X)", "know(Y)", "contrast(X,Y)"],
        "abstracted_from": "compound 'X and Y' (kin) + a CONTRAST over the genera",
        # the SURFACE family realizing this held comparison meaning. The head-led
        # form is the first surface; the meta-meta loop (cmsg110) APPENDS more
        # surfaces ('how does X differ from Y') as realizations of the SAME meaning.
        "surfaces": [],
    }
    # INSTALL: append the acquired construction as held graph data (idempotent —
    # do not double-install the same head).
    existing = {c["head"] for c in _ACQUIRED_QUESTION["comparison"]}
    if construction["head"] not in existing:
        _ACQUIRED_QUESTION["comparison"].append(construction)
    after = comprehend(example).grounded
    return {"acquired": (not before) and after, "construction": construction,
            "before": before, "after": after,
            "reason": ("the comparison construction now comprehends an example it "
                       "did not before" if (not before and after)
                       else "no before->after change")}


# ---------------------------------------------------------------------------
# THE META-META LOOP (cmsg110) — DIAGNOSE WHY THE GAP-DIAGNOSIS ITSELF FAILED.
#
# cmsg109's diagnose_comprehension_gap crosses 'compare X with Y' but a DIFFERENT
# surface of the SAME comparison — 'how does X differ from Y' — WALLS *and* the
# gap-diagnosis returns None (the ask-why itself fails: it names no construction).
# The user: "now have it diagnose why it couldn't name that gap." This is a
# RECURSION ON THE METACOGNITION — the agent introspects its OWN gap-diagnosis:
#
#   WHY couldn't the gap-diagnosis name the gap? Because diagnose_comprehension_gap
#   is SURFACE-BOUND: it names a gap only by matching HELD SURFACE FORMS (the head
#   verb 'compare'/'contrast' + a held connective). 'how does X differ from Y'
#   matches NO held head, so the diagnosis has nothing to anchor on — EVEN THOUGH
#   the question's MEANING is comparison, which the agent ALREADY HOLDS (the cmsg109
#   comparison construction). So the gap it could not name is NOT a missing MEANING;
#   it is a MISSING SURFACE OF A HELD MEANING.
#
# The FIX is the MEANING-vs-SURFACE distinction (the agent's prosody Mt at the GOAL
# level: a communicative FUNCTION is medium-independent, realized by medium-specific
# SERIALIZATIONS — here a comparison GOAL realized by MANY surface forms). A
# construction = ONE meaning + MANY surfaces; the agent acquires the new SURFACE as
# a realization of the HELD comparison goal (acquire_surface_variation), and
# comprehend_compare then recognizes the comparison MEANING across surfaces.
# ---------------------------------------------------------------------------

def diagnose_why_diagnosis_failed(question_text: str) -> Optional[dict]:
    """THE META-META — diagnose WHY diagnose_comprehension_gap could not name the gap
    (a recursion on the metacognition). Fires only when the question WALLS *and* the
    cmsg109 gap-diagnosis returns None (the ask-why itself failed) *and* the question
    carries the comparison MEANING the agent HOLDS in an unrecognized SURFACE.

    The agent introspects its OWN gap-diagnosis: it recognizes diagnose_comprehension_
    gap is SURFACE-BOUND — it anchors a gap on HELD SURFACE FORMS (the head verb
    'compare'/'contrast' + a held connective). This question matches NO held head, so
    the diagnosis has nothing to anchor on; BUT the question's MEANING is comparison
    (a 'difference'/'differ'/'vs' cue between two operands) — which the agent HOLDS.
    Returns the meta-meta diagnosis {why, mechanism='surface-bound', held_meaning,
    unrecognized_surface, operands, surface_template, fix} or None (the wall is NOT a
    held-meaning-in-an-unknown-surface — a genuinely-novel meaning the recursion
    cannot map, the next frontier).

    Faithful: a surface read (it detects the comparison MEANING cue + abstracts the
    SURFACE template the same way construction_grammar abstracts a construction-shape)
    over the agent's OWN gap-diagnosis — the metacognitive recursion, not new meaning."""
    # the gap-diagnosis (cmsg109) already failed iff it names nothing AND the surface
    # form does not parse — the precondition for the meta-meta (else cmsg109 handles it).
    if diagnose_comprehension_gap(question_text) is not None:
        return None  # cmsg109 named it — no recursion needed.
    toks = _tokens(question_text)
    if not toks:
        return None
    # the COMPARISON MEANING cue — a 'difference'/'differ'/'contrast'/'vs' marker
    # between two operands. This is the agent recognizing the MEANING (held) under a
    # surface its gap-diagnosis (head-bound) does not see. A surface read of the
    # meaning cue, NOT a head-verb match (that is exactly what was surface-bound).
    diff_cues = ("differ", "difference", "different", "distinguish", "versus", "vs")
    cue = next((c for c in diff_cues if c in toks), None)
    if cue is None:
        return None  # no comparison-MEANING cue -> a genuinely-novel wall (next frontier).
    # ABSTRACT the surface TEMPLATE the same closed family the agent holds covers:
    # find the operands around the cue/connective so the held meaning can be realized.
    tmpl = _abstract_surface_template(question_text)
    if tmpl is None:
        return None
    return {
        "mechanism": "surface-bound",
        "held_meaning": "comparison",
        "held_construction": "compare X with Y (cmsg109)",
        "unrecognized_surface": " ".join(toks),
        "surface_cue": cue,
        "operands": tmpl["operands"],
        "surface_template": tmpl["template"],
        "why": (
            "diagnose_comprehension_gap (my gap-diagnosis) is SURFACE-BOUND: it names "
            "a gap ONLY by matching HELD SURFACE FORMS (the head verb 'compare'/"
            "'contrast' + a held connective). This question matches NO held head, so "
            "the diagnosis had nothing to anchor on and returned None. BUT the "
            "question's MEANING is comparison (the " + repr(cue) + " cue between two "
            "operands) — the SAME comparison I ALREADY HOLD (the cmsg109 construction), "
            "in a SURFACE ('how does ... " + cue + " ...') I do not recognize. The gap "
            "I could not name is NOT a missing MEANING; it is a MISSING SURFACE OF A "
            "HELD MEANING."),
        "fix": (
            "the MEANING-vs-SURFACE distinction: a construction is ONE meaning realized "
            "by MANY surfaces (the prosody Mt's function-vs-serialization, at the goal "
            "level). Acquire the new surface template as a realization of the HELD "
            "comparison goal — comprehend the comparison MEANING across surfaces."),
    }


def _abstract_surface_template(question_text: str) -> Optional[dict]:
    """Abstract the SURFACE TEMPLATE + operands from an unrecognized comparison
    surface ('how does HTTP differ from FTP' -> template 'how does {x} differ from
    {y}', operands ['http','ftp']). Tries the held surface-vocab family first (the
    closed set the agent holds for the comparison meaning); on a match the operands
    fill the {x}/{y} slots and the template is the matched vocab form. A surface read
    of the meaning's realizations — the question-side analogue of the construction
    surface family. Returns None when no held surface family matches."""
    for template in _COMPARE_SURFACE_VOCAB:
        xy = _match_surface_template(template, question_text)
        if xy is not None:
            return {"template": template, "operands": [xy[0], xy[1]]}
    return None


def acquire_surface_variation(meta_diag: dict) -> dict:
    """SEEK/FIX (the meta-meta seek) — ACQUIRE the new SURFACE as a realization of the
    HELD comparison meaning. The meaning-vs-surface fix: a construction is ONE meaning
    + MANY surfaces, so the agent does NOT acquire a new meaning — it EXTENDS the held
    comparison construction with the new surface template ('how does {x} differ from
    {y}'), making the held comparison goal SURFACE-ROBUST. Mints the surface onto the
    held comparison construction (_ACQUIRED_QUESTION['comparison'][*]['surfaces']) so
    comprehend_compare recognizes the comparison MEANING across surfaces.

    Returns {acquired, surface_template, held_meaning, before, after, reason}:
    before/after is whether the meta-diag's example comprehends BEFORE/AFTER the
    acquire (the proof the surface frontier was crossed). Faithful: no new meaning is
    invented — the HELD comparison decomposition is reused; only the surface is added."""
    template = meta_diag["surface_template"]
    ops = meta_diag["operands"]
    example = template.replace("{x}", ops[0]).replace("{y}", ops[1])
    before = comprehend(example).grounded

    cons = _ACQUIRED_QUESTION.get("comparison") or []
    if not cons:
        # the held comparison meaning must exist (cmsg109 acquired it). If absent here,
        # install the canonical meaning so the surface has a meaning to realize.
        cons = [{
            "kind": "comparison", "head": _COMPARE_HEAD_VOCAB[0],
            "connectives": list(_COMPARE_CONNECTIVE_VOCAB),
            "decompose": list(_COMPARISON_MEANING),
            "abstracted_from": "the held comparison meaning (cmsg109)",
            "surfaces": [],
        }]
        _ACQUIRED_QUESTION["comparison"] = cons

    # EXTEND the HELD comparison construction with the new SURFACE (idempotent). The
    # surface realizes the SAME held decomposition — no new meaning acquired.
    target = cons[0]
    surfaces = target.setdefault("surfaces", [])
    if template not in surfaces:
        surfaces.append(template)

    after = comprehend(example).grounded
    return {
        "acquired": (not before) and after,
        "surface_template": template,
        "held_meaning": meta_diag["held_meaning"],
        "realizes": list(_COMPARISON_MEANING),
        "before": before, "after": after,
        "reason": (
            "the new SURFACE realizes the HELD comparison meaning "
            f"({' + '.join(_COMPARISON_MEANING)}) — no new meaning was acquired, only "
            "the surface was added; the comparison goal is now surface-robust"
            if (not before and after) else "no before->after change"),
    }


def comprehend_compare(question_text: str, *,
                       constructions: Optional[list[dict]] = None,
                       lexicon: Optional[list[dict]] = None,
                       _comprehend=None) -> Optional[list["TargetSpec"]]:
    """Recognize a COMPARISON question ('compare X with Y') + return its SUBGOAL
    TargetSpecs [know(X), know(Y), contrast], or None. Fires ONLY off an ACQUIRED
    comparison construction (_ACQUIRED_QUESTION) — until the metacognitive loop
    acquires it, a comparison question FRONTIERS (the honest wall). The two operands
    are each re-comprehended as KNOW leaves (KIN to the compound's subgoals); the
    CONTRAST is the added subgoal over the two grounded properties.

    A surface read of the acquired head + connective markers (NOT hardcoded compare
    behaviour); the meaning of each operand is its own KNOW comprehension. Returns
    None when no acquired comparison construction matches (the un-crossed frontier)."""
    cons_compare = _ACQUIRED_QUESTION.get("comparison") or []
    if not cons_compare:
        return None  # the construction is NOT yet acquired — frontier stands.
    text = (question_text or "").strip()
    toks = _tokens(text)
    if not toks:
        return None
    comp = _comprehend or comprehend

    def _build(x, y):
        """Build the [know(X), know(Y), contrast] subgoals for the held comparison
        meaning, or None if an operand does not ground as a KNOW leaf. The SAME
        decomposition for EVERY surface — the surface only differs in how (x, y)
        are read; the MEANING is held."""
        sx = comp("what is " + x, constructions=constructions, lexicon=lexicon)
        sy = comp("what is " + y, constructions=constructions, lexicon=lexicon)
        if not (sx.grounded and sx.kind == "know"
                and sy.grounded and sy.kind == "know"):
            return None
        contrast = TargetSpec(raw=f"contrast {x} with {y}", grounded=True,
                              kind="contrast")
        contrast.params = {"x": sx.know_concept, "y": sy.know_concept}
        return [sx, sy, contrast]

    for con in cons_compare:
        # SURFACE 1 — the head-led form ('compare X with Y' / 'contrast X and Y').
        head = con.get("head")
        if head and toks and toks[0] == _norm(head):
            conns = [_norm(c) for c in con.get("connectives", [])]
            conn = next((c for c in conns if c in toks[1:]), None)
            if conn is not None:
                ci = toks.index(conn, 1)
                x = " ".join(toks[1:ci]).strip()
                y = " ".join(toks[ci + 1:]).strip()
                if x and y:
                    built = _build(x, y)
                    if built is not None:
                        return built
        # SURFACE 2..n — the ACQUIRED SURFACE TEMPLATES ('how does {x} differ from
        # {y}'). These are SURFACES OF THE SAME held comparison meaning the meta-meta
        # loop acquired (the meaning-vs-surface fix); they decompose IDENTICALLY.
        for template in con.get("surfaces", []):
            xy = _match_surface_template(template, text)
            if xy is None:
                continue
            built = _build(*xy)
            if built is not None:
                return built
    return None


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _tokens(s: str) -> list[str]:
    return [t for t in re.split(r"\s+", _norm(s)) if t]


def _all_present(needles: list[str], hay_tokens: set[str]) -> bool:
    return all(_norm(n) in hay_tokens for n in needles)


def _extract_degree(relation_phrase: str) -> Optional[int]:
    """The DEGREE/DIMENSION the target asks for, read off the relation phrase ('12
    th dimensional', '1' in 'H 1'). The first integer in the phrase. None when the
    phrase names no degree. A surface read, not a meaning decision."""
    m = re.search(r"\b(\d+)\b", relation_phrase or "")
    return int(m.group(1)) if m else None


def _map_to_target(relation_phrase: str, object_phrase: str,
                   lexicon: list[dict]) -> Optional[dict]:
    """Map a comprehended (relation, object) frame -> {op, params} via the lexicon.
    The relation-phrase must contain all `match` fragments AND the object-phrase all
    `object_must` fragments (when present) for an entry to fire; the params are bound
    by matching object fragments. Returns None when no lexicon entry covers the frame
    (the comprehension frontier). A pure data lookup — no decision about meaning."""
    rel_tokens = set(_tokens(relation_phrase))
    obj_tokens = set(_tokens(object_phrase))
    for entry in lexicon:
        if not _all_present(entry.get("match", []), rel_tokens):
            continue
        omust = entry.get("object_must", [])
        if omust and not _all_present(omust, obj_tokens):
            continue
        params: dict[str, Any] = {}
        # bind each param from the first object-fragment rule that matches.
        for pname, rules in (entry.get("params") or {}).items():
            bound = None
            for rule in rules:
                if _all_present(rule.get("object_has", []), obj_tokens):
                    bound = rule.get("value")
                    break
            if bound is not None:
                params[pname] = bound
        # a degree/dimension param read off the relation phrase, when the op asks.
        if entry.get("degree_from_relation"):
            deg = _extract_degree(relation_phrase)
            if deg is not None:
                params["degree"] = deg
        return {"op": entry["op"], "params": params,
                "object_must_ok": True}
    return None


# ---------------------------------------------------------------------------
# formulate_ask(spec / prose) -> the AGENT'S OWN blocking question. The ASK
# action's QUESTION-FORMULATING faculty (the user's re-diagnosis: the agent CAN
# ask — it formulates the question from its OWN comprehension output; ASK only
# needed to be an ACTION). This is NOT a new reasoning faculty: it reads what
# `comprehend` ALREADY produced (the relation/object it parsed + the precise
# frontier reason: 'no target-op lexicon entry covers it' / 'no construction
# parsed'), plus what the CONSTRUCTION-PROSE machine (comprehend_gluing) failed
# to parse, and serializes that held stall-state into a SPECIFIC answerable
# question. The metacognition the cmsg141 run found 'missing' was never missing:
# the faculty output carries it; ASK just turns it into a posed question.
# ---------------------------------------------------------------------------

# the held GLUING cues the agent's reader handles in ONE shot (its held grammar:
# polygon side-identification + the projective plane). When the prose carries a held
# cue the gluing reader parses it directly — there is no unparsed-noun gap to raise.
# Read off comprehend_gluing's own held surfaces, NOT a hand table.
_GLUING_HELD_CUES = (["projective", "plane"], ["identifying", "side"])

# A GENERAL function-word / stopword set — domain-INDEPENDENT English glue (articles,
# prepositions, pronouns, conjunctions, determiners, copulas, quantifiers, the
# question/wh frame). This carries NO topology/construction vocabulary; it is the
# ordinary connective tissue of any English sentence. The agent strips it to leave
# the CONTENT words, then fails-to-parse the remainder against its held grammar. (No
# construction noun appears here — verify by inspection: a/an/the/of/into/... only.)
_STOPWORDS = frozenset("""
a an the of to into in on at by for from with within without and or but nor so yet
then than that this these those it its it's their them they he she him her his we us
our you your i me my mine ours yours theirs is are was were be been being am do does
did doing have has had having will would shall should can could may might must
each every all both either neither any some no none one two three four five six
seven eight nine ten single same other another such as if when while because since
about over under above below up down out off again further here there where which who
whom whose what why how not only just also very more most less least much many few
together counterpart counterparts s n th st nd rd point points part parts
""".split())

# the agent's HELD GLUING-GRAMMAR vocabulary — the surface words comprehend_gluing
# actually recognizes (the polygon names + the number-words it reads a side-count
# from + 'projective'/'plane'/'identifying'/'side'). A prose word IN this vocab is one
# the held reader already parses, so it is NOT a gap. Read off construction_operators
# (the live held grammar), NOT a hand list of construction nouns.
def _held_gluing_vocab() -> set[str]:
    held: set[str] = set()
    for cue in _GLUING_HELD_CUES:
        held.update(cue)
    try:
        from domains import construction_operators as _co
        held.update(k.lower() for k in getattr(_co, "_POLYGON_SIDES", {}))
        held.update(k.lower() for k in getattr(_co, "_NUMBER_WORDS", {}))
        # the nouns ALREADY incorporated (the ASK incorporate step extends this) are
        # no longer gaps — the reader recognizes them now. This is what makes each ASK
        # ADVANCE the goal: an incorporated noun drops out, so the next ASK names the
        # NEXT gap. Multi-word aliases ('leg opening') contribute their tokens too.
        for n in getattr(_co, "_RECOGNIZED_NOUNS", set()):
            held.update(_tokens(n))
    except Exception:
        pass
    return held


def name_unparsed_constructions(prose: str,
                                *, parsed_phrases: tuple[str, ...] = ()) -> list[str]:
    """The agent's gluing reader, on a '' parse, DISCOVERS which content-words it could
    not turn into a held structure — GENERALLY, by tokenize-minus-(stopwords + held-
    grammar-terms), NOT by matching any curated construction/topology list.

    THE DISCOVERY (no donkey tail): the prose is tokenized; the GENERAL stopwords (a/
    an/the/of/into/... — domain-independent glue) are removed; the agent's HELD grammar
    terms are removed (the gluing-grammar vocab _held_gluing_vocab + the relation/object
    phrases the question construction ALREADY parsed, passed as `parsed_phrases`); what
    REMAINS are the CONTENT words the held gluing grammar cannot parse into a structure
    — the agent's OWN discovered gaps. The faculty also confirms the prose did not parse
    as a held gluing (comprehend_gluing '' / no held cue), so a held construction does
    not raise a spurious gap.

    HONEST: this is GENERAL discovery, so the remainder may include NOISE (ordinary
    content words the agent cannot parse — 'pair'/'point') alongside the real gaps; the
    parent's one-step answers / the self-verify handle that. There is NO construction or
    topology noun list anywhere here — the ONLY vocabulary is the general stopwords +
    the agent's actual held-grammar terms. The gaps are DISCOVERED (tokenize + fail-to-
    parse), not matched."""
    d = (prose or "").lower()
    if not d.strip():
        return []
    # if a HELD gluing cue is present the reader parses it directly — no gap to raise.
    if any(all(tok in d for tok in cue) for cue in _GLUING_HELD_CUES):
        return []
    # the held-grammar terms to strip: the gluing-grammar vocab + the tokens of every
    # phrase the question construction ALREADY parsed (the relation 'fundamental group'
    # + the object 'this topological space' — comprehended, so NOT a gluing gap).
    held = _held_gluing_vocab()
    for ph in parsed_phrases:
        held.update(_tokens(ph))
    # TOKENIZE - STOPWORDS - HELD: the remaining content words are the discovered gaps.
    found: list[str] = []
    for tok in _tokens(d):
        if tok in _STOPWORDS or tok in held:
            continue
        if not tok.isalpha():            # drop bare numerals/punctuation residue.
            continue
        if tok in found:
            continue
        found.append(tok)
    return found


def formulate_ask(spec: "TargetSpec", *, prose: Optional[str] = None
                  ) -> Optional[dict]:
    """FORMULATE the AGENT'S blocking question from its OWN comprehension stall —
    the ASK action's question faculty. Given a stalled TargetSpec (grounded=False)
    + the construction prose, serialize what the agent comprehended vs what it LACKS
    into a SPECIFIC, answerable, one-step question. Returns {question, want, kind,
    parsed, lacked} or None (the comprehension did not even reach a nameable stall —
    a deeper, still-silent gap).

    The question is the AGENT's: every field is read off the faculty output
    (spec.relation_phrase / spec.object_phrase / spec.reason) + the gluing reader's
    named unparsed constructions. The shell does NOT author it.

    Two stall shapes, both the agent's own output:
      · TARGET-OP frontier (comprehend parsed the relation+object but no lexicon
        entry covers it): the agent knows WHAT it is asked (the relation 'X of Y')
        but holds no target OP for that relation -> ask for the operator name.
      · CONSTRUCTION-PROSE frontier (the gluing reader returned '' on the prose):
        the agent names the unparsed construction-nouns it lacks an operator for
        -> ask for the operator that builds the named construction.
    """
    if spec is None or spec.grounded:
        return None
    rel = (spec.relation_phrase or "").strip()
    obj = (spec.object_phrase or "").strip()

    # CONSTRUCTION-PROSE stall — the gluing reader named unparsed construction nouns.
    # This is the prose->structure wall the experiment targets: the agent comprehends
    # the ASK (the relation 'fundamental group') but the OBJECT is given by a
    # CONSTRUCTION its gluing reader cannot parse. The question asks for the operator
    # that turns the construction into something the held machinery can carry.
    # the relation/object the question construction ALREADY parsed are NOT gluing gaps
    # — strip their tokens from the general discovery so they do not show as unparsed.
    parsed_phrases = tuple(p for p in (rel, obj) if p)
    nouns = (name_unparsed_constructions(prose, parsed_phrases=parsed_phrases)
             if prose else [])
    if nouns and rel:
        named = ", ".join(repr(n) for n in nouns[:6])
        q = (f"I am pursuing the {rel} of a space given by a CONSTRUCTION; my "
             f"construction-prose reader returned the empty word on it — it does "
             f"not parse the construction-noun(s) {named}. I hold the polygon-word "
             f"reader (side-identification + the projective plane) and the held "
             f"homology/pi_1 tower. What is the operator that turns this "
             f"construction into a space my held machinery can carry (a CW "
             f"description / a known space it is homotopy-equivalent to)?")
        return {"question": q, "kind": "construction_operator",
                "want": "operator_for_construction", "parsed": rel,
                "lacked": nouns}

    # TARGET-OP frontier — the agent parsed the relation+object but holds no op.
    if rel and "no target-op lexicon entry" in (spec.reason or ""):
        q = (f"I comprehended the question as asking for the {rel!r} of "
             f"{obj!r}, but I hold no target OPERATION mapped to the relation "
             f"{rel!r}. What is the formal target operation (the op name) I "
             f"should pursue for the {rel!r} of a space?")
        return {"question": q, "kind": "target_op",
                "want": "target_op_for_relation", "parsed": rel, "lacked": [rel]}

    # the comprehension did not reach a nameable stall (no relation parsed) — a
    # still-silent gap the agent cannot yet articulate (honest None).
    return None


# ---------------------------------------------------------------------------
# comprehend(question_text) -> TargetSpec — the front door.
# ---------------------------------------------------------------------------

def comprehend(question_text: str, *, question_id: Optional[str] = None,
               constructions: Optional[list[dict]] = None,
               lexicon: Optional[list[dict]] = None,
               substrate=None) -> TargetSpec:
    """COMPREHEND a RAW question text into a formal TargetSpec the elevator ascends.

    READ (plainify the LaTeX) -> COMPREHEND (the held construction grammar parses a
    question sentence into the relation frame {event=target-operation, patient=object})
    -> MAP (the target-op lexicon -> the formal op + params). Returns a grounded
    TargetSpec, or one with grounded=False + the precise gap (the comprehension
    frontier: no question construction parsed, or no lexicon entry covered the
    relation/object). NEVER a faked target.

    `substrate` is accepted so a host may mint the Question node before calling (the
    driver does); the comprehension itself reads only the held graph-data
    constructions + lexicon — it owns no agent state."""
    cons = constructions or _cg.load_constructions()
    lex = lexicon or load_lexicon()
    spec = TargetSpec(question_id=question_id, raw=question_text or "")

    # RECOGNIZE A COMPOUND GOAL first: a question joining >= 2 sub-questions with a
    # clause connective ('what is X and compute Y') DECOMPOSES into SUBGOALS (each a
    # recursively-comprehended LEAF of its own kind — a KNOW subgoal + a COMPUTE
    # subgoal -> MIXED faculties). drive() does NOT route it — it seeds the COMPOUND
    # goal; the pursuit decomposes it (seeds a child Goal per subgoal, pursues each
    # recursively, composes). comprehend_compound is STRICT (>= 2 grounded leaves),
    # so a flat question with an incidental 'and' falls through to the flat parse.
    subgoals = comprehend_compound(question_text, constructions=cons, lexicon=lex)
    if subgoals is not None:
        spec.kind = "compound"
        spec.subgoals = subgoals
        spec.grounded = True
        spec.reason = ("comprehended -> COMPOUND goal: decompose into "
                       + ", ".join(f"{sg.kind}({sg.op or sg.know_concept})"
                                   for sg in subgoals)
                       + " (mixed-faculty subgoals, pursued recursively)")
        return spec

    # RECOGNIZE A COMPARISON GOAL ('compare X with Y'): fires ONLY off an ACQUIRED
    # comparison construction (the metacognitive loop's seek-to-understand minted
    # it). Until acquired this returns None and the question FRONTIERS (the honest
    # wall the ask-why diagnoses). The comparison goal decomposes into [know(X),
    # know(Y), contrast] — the cmsg108 compound's kin, plus the added CONTRAST.
    cmp_subgoals = comprehend_compare(question_text, constructions=cons, lexicon=lex)
    if cmp_subgoals is not None:
        spec.kind = "compare"
        spec.subgoals = cmp_subgoals
        spec.grounded = True
        knows = [sg.know_concept for sg in cmp_subgoals if sg.kind == "know"]
        spec.reason = (f"comprehended -> COMPARISON goal (acquired construction): "
                       f"contrast {' vs '.join(knows)} — subgoals know(X) + "
                       f"know(Y) + contrast, pursued recursively")
        return spec

    # RECOGNIZE THE KIND first: a SELF/META question (ABOUT THE AGENT — 'how do
    # YOU retrieve', 'where is YOUR frontier', 'what do YOU need to compute X')
    # routes to a REFLECTIVE faculty, NOT the elevator. Checked before the
    # world-construction parse: a meta question's shape ('how do you ...') is not
    # a 'Compute the X of Y' world frame, so the world parse would frontier on it.
    meta = comprehend_meta(question_text)
    if meta is not None:
        spec.kind = "meta"
        spec.meta_target = meta["meta_target"]
        spec.faculty = meta["faculty"]
        spec.meta_arg = meta.get("meta_arg")
        spec.grounded = True
        spec.reason = (f"comprehended -> SELF/META question (meta_target="
                       f"{spec.meta_target}, faculty={spec.faculty}"
                       + (f", arg={spec.meta_arg!r}" if spec.meta_arg else "")
                       + ") via the held meta-target lexicon")
        return spec

    # RECOGNIZE A KNOW GOAL: a bare definitional ask ('what is X') seeds the goal
    # 'know X'. drive() does NOT route it — it seeds the goal; the pursuit grounds
    # X via the reference wall (wiki_local). comprehend_know fires only when the
    # tail does NOT map to a world target-op (a compute goal is the world parse's),
    # so the world question keeps priority. The self/meta case already returned.
    know = comprehend_know(question_text, lexicon=lex)
    if know is not None:
        spec.kind = "know"
        spec.know_concept = know
        spec.grounded = True
        spec.reason = (f"comprehended -> KNOW goal know({know!r}) — the pursuit "
                       f"grounds it via the reference wall (wiki_local)")
        return spec

    plain = plainify(question_text)
    # find the QUESTION sentence: the first sentence a question construction parses
    # (the imperative 'Compute ...' / interrogative 'What is ...'); a leading 'Let X
    # be ...' preamble sentence is context the construction skips by not matching.
    frame = None
    chosen = ""
    for sent in _split_sentences(plain) or [plain]:
        # strip a trailing terminal punctuation the matcher does not need.
        f = _cg.apply_constructions(sent.rstrip(".!"), cons)
        if f and isinstance(f, dict) and f.get("event"):
            frame, chosen = f, sent
            break
    if frame is None:
        spec.reason = ("no question construction parsed the prose (the comprehension "
                       "frontier — a question SHAPE the held constructions do not "
                       "cover; add a construction)")
        return spec

    relation_phrase = str(frame.get("event") or "")
    object_phrase = str(frame.get("patient") or "")
    spec.relation_phrase = relation_phrase
    spec.object_phrase = object_phrase
    spec.comprehended = frame

    mapped = _map_to_target(relation_phrase, object_phrase, lex)
    if mapped is None:
        spec.reason = (f"comprehended (relation={relation_phrase!r}, "
                       f"object={object_phrase!r}) but no target-op lexicon entry "
                       f"covers it (the comprehension frontier — add a lexicon "
                       f"entry mapping this relation-phrase to a target op)")
        return spec

    spec.op = mapped["op"]
    spec.params = mapped["params"]
    spec.grounded = True
    spec.reason = (f"comprehended -> target {spec.op}({spec.params}) via the held "
                   f"construction grammar + the target-op lexicon")
    return spec


__all__ = ["comprehend", "TargetSpec", "plainify", "load_lexicon",
           "comprehend_meta", "load_meta_lexicon", "comprehend_know",
           "comprehend_compound", "comprehend_compare",
           "diagnose_comprehension_gap", "acquire_compare_construction",
           "diagnose_why_diagnosis_failed", "acquire_surface_variation",
    "formulate_ask", "name_unparsed_constructions"]

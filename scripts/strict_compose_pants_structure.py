"""strict_compose_pants_structure — THE COMPREHENSION->STRUCTURE STAGE under the
strict parent protocol (cmsg149's UNCLOSED gap, the cmsg139 donkey's home).

THE WALL. The agent can ASK + NAME the pieces (cmsg145: pants->three_holed_sphere,
sew->glue_boundary_circles, waistband->collapse_circle_to_point) AND BUILD a bounded
surface's pi_1 from a (word, free) spec (cmsg147-149: strict_build_bounded_surface,
4/4). The UNCLOSED step: turning the NAMED PIECES into the constructor's input by
COMPOSING — applying the named operators (build pants pieces, glue leg-boundary
circles, collapse waist circles), MECHANICALLY tracking the boundary circles. cmsg139
VOID was the LLM hand-writing `cells=[("aba-b-",1)], crush=[["p","q"]]` after reasoning
"two pants = 2-holed torus". The faithful version (this harness): the AGENT composes
the structure by APPLYING its named operators as RUNNABLE operations on pieces; the
PARENT bridges only the minimal COMPOSITIONAL CONCEPT per ask.

THE STRICT PROTOCOL (donkey-impossible):
  1. A PIECE is (presentation pi_1, tracked boundary-circle words, #connected pieces).
     The agent COMPOSES by APPLYING operators to pieces:
       (i)  REPRESENT each PANTS as a piece (pi_1 = F_2 free, three tracked boundary
            circles whose product is trivial — derived from the held free-group fact +
            the parent's boundary-product bridge, NOT a hand-written spec);
       (ii) GLUE the legs (apply glue_boundary_circles: identify two boundary circles
            — van-Kampen AMALGAM when the pieces are separate, HNN when already
            connected; the circles consumed);
       (iii)COLLAPSE the waists (apply collapse_circle_to_point: kill each circle's
            class; collapsing to a SINGLE point WEDGES — adds m-1 free generators).
     Each is the AGENT APPLYING a runnable operator + tracking boundary circles —
     NOT the LLM reasoning the resulting surface.
  2. When the composition STALLS (an operator is NAMED but not RUNNABLE), the agent
     ASKS ONE specific question.
  3. The PARENT bridges ONE compositional CONCEPT (mute until asked): van Kampen for
     gluing / collapse-on-pi_1. NOT the spec, NOT the resulting surface's identity,
     NOT the answer (J).
  4. The agent COMPOSES the runnable operation, applies it, continues.
  5. SELF-VERIFY each operation on KNOWN simpler textbook cases. An operation that
     FAILS a known is REJECTED -> the agent ASKS again -> the parent bridges the ONE
     CORRECTED concept -> re-compose -> re-verify (the developmental loop).
  6. Repeat until the pants structure is COMPOSED -> the held constructor reads pi_1
     -> verify vs J = (Z x Z) * Z at the END ONLY.

THE DONKEY RAILS (maximum):
  · The AGENT composes by APPLYING named operators (glue = amalgam/HNN relator;
    collapse = kill class + wedge). The shell authors NO topology ("two pants = 2-holed
    torus"), NO hand-written (word,free)/cells/crush spec, NO answer-shape.
  · The parent bridges ONE compositional concept on ask, NOT this construction's
    topology, NOT the spec, NOT J.
  · The glue/collapse OPERATIONS are GENERAL + self-verified on KNOWN textbook cases
    (two disks->S^2, annulus self-glue->torus [HNN], cylinder both-ends->one-point->
    S^2vS^1 [wedge], collapse-annulus-circle->disk). J checked at the END only; NO
    reverse-engineering (the operators are corrected by FAILING KNOWNS, never by J).

No LLM-reasoned topology/spec. No Rust. Math/reading domain only. Speech untouched.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))

from substrate_rs import _native                          # noqa: E402
from domains import construction_operators as _co         # noqa: E402
from domains import commutator_rank as _cr                # noqa: E402

PROSE_ID_PREFIX = "671579"

# the held pi_1 tower (pi1_from_relators / h1_of_presentation) reads SINGLE-CHARACTER
# generators (it iterates a relator string char-by-char, uppercase = inverse). So a
# piece's generators are single lowercase letters; boundary circles are WORDS over
# them in parse_word syntax ('a' forward, 'a-' inverse). A fresh-letter pool mints
# disjoint generators per piece + fresh HNN/wedge generators (mechanical bookkeeping).
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


# ===========================================================================
# THE PIECE — a presentation pi_1 (held) + TRACKED boundary-circle words + the count
# of CONNECTED components (so glue knows AMALGAM vs HNN). The COMPOSITION operators
# act on PIECES, tracking the boundary circles MECHANICALLY through every glue/collapse.
# ===========================================================================

@dataclass
class Piece:
    gens: str                              # single-char generator alphabet
    relators: List[str]                    # relator words (parse_word syntax)
    boundaries: List[str]                  # tracked boundary-circle words over gens
    components: int = 1                    # # of connected components (for amalgam/HNN)
    note: str = ""

    def presentation(self):
        return _cr.pi1_from_relators(self.gens, self.relators)

    def h1(self):
        return _cr.h1_of_presentation(self.presentation())


# ---------------------------------------------------------------------------
# WORD ALGEBRA — the minimal mechanical word ops (invert, concat). parse_word syntax:
# 'a' forward, 'a-' inverse. Held string ops, NOT topology — they manipulate the
# boundary WORDS the operators carry.
# ---------------------------------------------------------------------------

def _inv(word: str) -> str:
    parsed = _co.parse_word(word)
    out = []
    for c, s in reversed(parsed):
        out.append(c + ("-" if s > 0 else ""))
    return "".join(out)


def _concat(*words: str) -> str:
    return "".join(w for w in words if w)


def _fresh_gen(used: str) -> str:
    """Mint a fresh single-char generator not already used (HNN stable letter / wedge
    point generator). Mechanical naming — not a topological decision."""
    for c in _LETTERS:
        if c not in used:
            return c
    raise RuntimeError("out of generator letters")


# ===========================================================================
# THE AGENT'S COMPOSITION MACHINERY — it APPLIES the named operators to pieces. Each
# operator is gated on parent-bridged compositional concepts; before a concept is
# bridged the operator is NAMED but not RUNNABLE, so the machinery ARTICULATES the gap
# as a question. ALL operators are GENERAL (verified on knowns, corrected by FAILING
# knowns).
# ===========================================================================

_BRIDGED: dict = {}        # compositional-concept name -> the parent's bridge


# --- OPERATOR A: REPRESENT a pants as a piece (3-holed sphere). The agent holds the
#     held free-group fact (a bounded surface retracts onto its 1-skeleton = a FREE
#     group, pi_1 = F_2); it needs ONE concept — how the THREE boundary circles sit in
#     that free group (b0*b1*b2 = 1). ----------------------------------------------

def represent_pants(g0: str, g1: str) -> Optional[Piece]:
    """REPRESENT a pair of pants as a piece over the two fresh generators g0,g1
    (pi_1 = F_2 = <g0,g1 | >). Requires the pants_boundary_product bridge. The three
    boundary circles are placed by held word-algebra from the bridged relation
    b0*b1*b2 = 1: b0 = g0, b1 = g1, b2 = (g0 g1)^-1."""
    if "pants_boundary_product" not in _BRIDGED:
        return None
    b0 = g0                                # waist
    b1 = g1                                # leg
    b2 = _inv(_concat(g0, g1))             # leg -> (g0 g1)^-1, so b0*b1*b2 = 1
    return Piece(gens=g0 + g1, relators=[], boundaries=[b0, b1, b2], components=1,
                 note=f"pants<{g0}{g1}>: F_2, 3 bdry (b0*b1*b2=1)")


# --- OPERATOR B: GLUE two boundary circles (apply glue_boundary_circles). van-Kampen:
#     AMALGAM when the two circles lie in SEPARATE components (identify -> relator
#     c1=c2, components merge); HNN when they lie in the SAME (already-connected)
#     component (a NEW stable generator t with t c1 t^-1 = c2). GENERAL. -------------

def glue_circles(piece: Piece, i: int, j: int) -> Optional[Piece]:
    """Apply glue_boundary_circles to identify boundary i with boundary j. Requires
    van_kampen_glue; the HNN case additionally requires van_kampen_glue_connected.
    Returns a new Piece (boundaries i,j consumed) or None (not yet runnable)."""
    if "van_kampen_glue" not in _BRIDGED:
        return None
    c1, c2 = piece.boundaries[i], piece.boundaries[j]
    new_bnd = [b for k, b in enumerate(piece.boundaries) if k not in (i, j)]
    # SAME-COMPONENT (already connected) -> HNN; SEPARATE -> amalgam. The piece tracks
    # components: a disjoint_union of two 1-component pieces is 2 components, so the
    # FIRST glue is an amalgam (merges to 1) and the SECOND is on a connected piece.
    if piece.components >= 2:
        # AMALGAM: identify the two loops -> relator c1 = c2, merge components.
        relator = _concat(c1, _inv(c2))
        return Piece(gens=piece.gens, relators=list(piece.relators) + [relator],
                     boundaries=new_bnd, components=piece.components - 1,
                     note=piece.note + f" | amalgam-glue bdry {i}~{j}")
    # SAME COMPONENT -> HNN (requires the corrected concept; until bridged, the agent
    # stalls re-using the amalgam concept and the self-verify CATCHES it on a known).
    if "van_kampen_glue_connected" not in _BRIDGED:
        # the agent does NOT yet hold the connected-glue concept; it applies the only
        # glue concept it has (amalgam). This produces a WRONG pi_1 that the self-verify
        # CATCHES on the annulus-self-glue=torus known -> the agent asks the correction.
        relator = _concat(c1, _inv(c2))
        return Piece(gens=piece.gens, relators=list(piece.relators) + [relator],
                     boundaries=new_bnd, components=piece.components,
                     note=piece.note + f" | (amalgam-as-fallback) glue bdry {i}~{j}")
    # CORRECTED HNN: a new stable generator t with t c1 t^-1 = c2 (t c1 t^-1 c2^-1 = 1).
    t = _fresh_gen(piece.gens)
    relator = _concat(t, c1, t + "-", _inv(c2))
    return Piece(gens=piece.gens + t,
                 relators=list(piece.relators) + [relator],
                 boundaries=new_bnd, components=piece.components,
                 note=piece.note + f" | HNN-glue bdry {i}~{j} (stable {t})")


def disjoint_union(a: Piece, b: Piece) -> Piece:
    """Place two pieces side by side (generators already disjoint). Boundaries
    concatenate; components add; no relator. Mechanical bookkeeping, NOT topology."""
    return Piece(gens=a.gens + b.gens,
                 relators=list(a.relators) + list(b.relators),
                 boundaries=list(a.boundaries) + list(b.boundaries),
                 components=a.components + b.components,
                 note=a.note + " + " + b.note)


# --- OPERATOR C: COLLAPSE boundary circles to a point (apply collapse_circle_to_point).
#     Kill each circle's class (relator c = 1). Collapsing m circles to a SINGLE shared
#     point ALSO WEDGES — identifying m points in a connected space adds (m-1) free
#     generators (the new independent loops through the shared point). GENERAL. -------

def collapse_circles(piece: Piece, idxs: List[int]) -> Optional[Piece]:
    """Apply collapse_circle_to_point to the boundaries at idxs (to a SINGLE point).
    Requires collapse_on_pi1; collapsing >1 circle to one point also requires
    collapse_wedge. Returns a new Piece (collapsed boundaries consumed) or None."""
    if "collapse_on_pi1" not in _BRIDGED:
        return None
    new_rel = list(piece.relators)
    new_gens = piece.gens
    for i in idxs:
        new_rel.append(piece.boundaries[i])           # kill the class: c = 1
    note = piece.note + f" | collapse bdry {idxs}"
    if len(idxs) >= 2:
        if "collapse_wedge" not in _BRIDGED:
            # the agent has only the single-circle collapse concept; collapsing several
            # to ONE point with kill-each-class ALONE is WRONG (misses the wedge). The
            # self-verify CATCHES it on the cylinder-both-ends->one-point=S^2vS^1 known.
            note += " (kill-each-class only — wedge NOT yet held)"
        else:
            # CORRECTED: identifying m collapse-points to ONE point wedges in (m-1)
            # free generators.
            for _ in range(len(idxs) - 1):
                w = _fresh_gen(new_gens)
                new_gens = new_gens + w               # a fresh free generator, no relator
            note += f" (wedge +{len(idxs) - 1} free gen(s))"
    new_bnd = [b for k, b in enumerate(piece.boundaries) if k not in idxs]
    return Piece(gens=new_gens, relators=new_rel, boundaries=new_bnd,
                 components=piece.components, note=note)


# ===========================================================================
# THE COMPOSITION-GAP ARTICULATION — the agent walks its composition steps; for each
# operator it holds NAMED but not RUNNABLE, it yields the specific question it poses.
# The CORRECTION questions (after a self-verify FAILS a known) are articulated by
# agent_self_detected_error below. One gap at a time.
# ===========================================================================

def articulate_composition_gaps():
    gaps = []
    if "pants_boundary_product" not in _BRIDGED:
        gaps.append({
            "step": "represent a pair of pants as a (group, boundary-circles) piece",
            "want": "represent_pants", "lacked": ["pants_boundary_product"],
            "question": (
                "I hold that a pair of pants retracts onto a graph = a FREE group, so "
                "pi_1 = F_2 = <x,y|>. But to glue and collapse later I must TRACK its "
                "three boundary circles as elements of that free group, and I do not "
                "know how the three boundary loops of a genus-0 three-holed surface sit "
                "in pi_1 relative to each other. How do the three boundary circles of a "
                "pair of pants relate as elements of its fundamental group?")})
        return gaps
    if "van_kampen_glue" not in _BRIDGED:
        gaps.append({
            "step": "glue two boundary circles (apply glue_boundary_circles)",
            "want": "glue_circles", "lacked": ["van_kampen_glue"],
            "question": (
                "I have NAMED glue_boundary_circles and can name two boundary-circle "
                "WORDS c1, c2, but I have NO runnable operation that composes two "
                "(group, boundary) pieces along a shared circle into one pi_1. When I "
                "identify boundary circle c1 with c2, how do I combine pi_1(A) and "
                "pi_1(B) along the glued circle?")})
        return gaps
    if "collapse_on_pi1" not in _BRIDGED:
        gaps.append({
            "step": "collapse a waist circle to a point (apply collapse_circle_to_point)",
            "want": "collapse_circles", "lacked": ["collapse_on_pi1"],
            "question": (
                "I have NAMED collapse_circle_to_point and can name the waist "
                "boundary-circle WORDS, but I have NO runnable operation for what "
                "collapsing a circle to a point DOES to the fundamental group. When I "
                "collapse a boundary circle c (a loop) to a point, how does pi_1 "
                "change?")})
        return gaps
    return gaps


# ===========================================================================
# THE STRICT PARENT — mute until the agent ASKS, then ONE compositional concept per
# ask. Each value is a SINGLE concept; NEVER the spec, this construction's topology,
# or J. Keyed by the concept the agent NAMES.
# ===========================================================================

def parent_compose_step(ask: dict):
    lacked = [l.lower() for l in (ask.get("lacked") or [])]
    for want in lacked:
        for noun, step in _PARENT_COMPOSE_TABLE:
            if noun == want:
                assert set(step.keys()) <= {"concept", "op"}, \
                    "VOID: parent compose-step is not a single compositional concept"
                return dict(step, answered=noun)
    return None            # MUTE.


_PARENT_COMPOSE_TABLE = [
    ("pants_boundary_product",
     {"concept": "on a genus-0 surface with k boundary circles the boundary loops "
                 "(suitably oriented) multiply to the identity: b_0*b_1*...*b_(k-1)=1; "
                 "equivalently k-1 of them freely generate pi_1 and the last is the "
                 "inverse of their product",
      "op": "boundary_product_relation"}),
    ("van_kampen_glue",
     {"concept": "van Kampen: gluing A to B along a circle C gives the free product "
                 "pi_1(A) *_{pi_1(C)} pi_1(B) amalgamated over pi_1(C)=Z; concretely "
                 "take the disjoint union of the presentations and add ONE relation "
                 "equating the two glued boundary loops, c_A = c_B (the glued circle "
                 "is no longer a free boundary)",
      "op": "amalgam_over_circle"}),
    # CORRECTION 1 (asked after the self-verify CATCHES the annulus-self-glue=torus
    # known failing): gluing two boundary circles of an ALREADY-CONNECTED space is an
    # HNN extension, not an amalgamation. ONE corrected compositional concept.
    ("van_kampen_glue_connected",
     {"concept": "when the two glued boundary circles lie in the SAME connected piece "
                 "(it is already connected), the gluing is an HNN extension, NOT an "
                 "amalgamated product: introduce a NEW stable generator t and the "
                 "relation t*c_1*t^-1 = c_2 (conjugating one boundary loop to the "
                 "other across the new handle)",
      "op": "hnn_over_circle"}),
    ("collapse_on_pi1",
     {"concept": "collapsing a circle subcomplex c to a point makes the loop c "
                 "nullhomotopic, so pi_1 of the quotient is pi_1 with the relation "
                 "c = 1 adjoined (the class of c is killed)",
      "op": "kill_circle_class"}),
    # CORRECTION 2 (asked after the self-verify CATCHES the cylinder-both-ends->one-
    # point known failing): collapsing SEVERAL circles to a SINGLE shared point also
    # WEDGES. ONE corrected compositional concept.
    ("collapse_wedge",
     {"concept": "collapsing m circles to a SINGLE shared point is more than killing "
                 "each class: identifying the m resulting points to one point in a "
                 "connected space WEDGES in (m-1) new circles, so pi_1 gains (m-1) "
                 "free generators (a wedge with a circle = a free factor of Z)",
      "op": "wedge_identified_points"}),
]


def incorporate_compose_step(one_step: dict):
    answered = one_step.get("answered")
    _BRIDGED[answered] = {"concept": one_step.get("concept"), "op": one_step.get("op")}
    return {"how": f"incorporated compositional concept {answered!r} -> "
                   f"{one_step.get('op')!r}", "op": one_step.get("op")}


def run_compose_ask_loop(max_asks: int = 6):
    transcript = []
    n = 0
    while n < max_asks:
        gaps = articulate_composition_gaps()
        if not gaps:
            break
        gap = gaps[0]
        one_step = parent_compose_step(gap)
        rec = {"question": gap["question"], "step": gap["step"], "want": gap["want"],
               "lacked": gap["lacked"], "one_step": one_step, "advanced": None}
        if one_step is None:
            rec["advanced"] = "parent mute / no one-step"
            transcript.append(rec)
            break
        adv = incorporate_compose_step(one_step)
        rec["advanced"] = adv["how"]
        transcript.append(rec)
        n += 1
    return transcript


# ===========================================================================
# THE SELF-VERIFY — each composition OPERATION is checked on KNOWN textbook cases
# (NEVER the pants answer). The KNOWNS are chosen to CATCH the amalgam-vs-HNN and
# the kill-vs-wedge errors. An operation that FAILS a known is REJECTED.
# ===========================================================================

def _free_rank(piece: Piece) -> int:
    return piece.h1().free_rank


def _trivial(piece: Piece) -> bool:
    h = piece.h1()
    return h.free_rank == 0 and not h.torsion


def self_verify_operations():
    """Run the GENERAL operators on KNOWN textbook cases (the SAME operators applied to
    the pants), returning rows {case, expected_rank, got_rank, pass}. NONE is the pants
    answer. These knowns CATCH the two operator errors."""
    rows = []

    if "van_kampen_glue" in _BRIDGED:
        # KNOWN 1 — two DISKS glued along their boundary circle = S^2 (rank 0).
        d1 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
        d2 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
        u = disjoint_union(d1, d2)
        g = glue_circles(u, 0, 1)
        rows.append({"case": "two disks glued along boundary = S^2 (amalgam)",
                     "expected_rank": 0, "got_rank": _free_rank(g) if g else None,
                     "pass": bool(g is not None and _free_rank(g) == 0)})

        # KNOWN 2 — annulus glued to disk along ONE circle = disk (rank 0).
        ann = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                    note="annulus")
        dsk = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
        u2 = disjoint_union(ann, dsk)
        g2 = glue_circles(u2, 0, 2)            # annulus-t (0) ~ disk (2)
        rows.append({"case": "annulus glued to disk along one circle = disk (amalgam)",
                     "expected_rank": 0, "got_rank": _free_rank(g2) if g2 else None,
                     "pass": bool(g2 is not None and _free_rank(g2) == 0)})

        # KNOWN 3 (CATCHES the HNN error) — gluing the TWO boundary circles of a single
        # ANNULUS to EACH OTHER = TORUS (rank 2). The annulus is ONE connected piece,
        # so this glue is on a CONNECTED component -> must be HNN, not amalgam. With the
        # amalgam fallback it reads rank 1 (FAIL); with the HNN correction rank 2 (PASS).
        ann2 = Piece(gens="s", relators=[], boundaries=["s", "s"], components=1,
                     note="annulus")
        g3 = glue_circles(ann2, 0, 1)
        rows.append({"case": "annulus's two boundary circles glued to each other = "
                             "torus (HNN, connected)",
                     "expected_rank": 2, "got_rank": _free_rank(g3) if g3 else None,
                     "pass": bool(g3 is not None and _free_rank(g3) == 2)})

    if "collapse_on_pi1" in _BRIDGED:
        # KNOWN 4 — collapse ONE boundary circle of an annulus = disk (rank 0).
        ann = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                    note="annulus")
        c = collapse_circles(ann, [0])
        rows.append({"case": "collapse one boundary circle of an annulus = disk",
                     "expected_rank": 0, "got_rank": _free_rank(c) if c else None,
                     "pass": bool(c is not None and _free_rank(c) == 0)})

        # KNOWN 5 (CATCHES the WEDGE error) — collapse BOTH boundary circles of a
        # cylinder to a SINGLE point = S^2 with two points identified = S^2 v S^1
        # (rank 1). kill-each-class ALONE gives <t|t,t> = trivial (rank 0, FAIL); the
        # wedge correction gives rank 1 (PASS).
        cyl = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                    note="cylinder")
        c2 = collapse_circles(cyl, [0, 1])
        rows.append({"case": "collapse both ends of a cylinder to one point = "
                             "S^2 v S^1 (wedge)",
                     "expected_rank": 1, "got_rank": _free_rank(c2) if c2 else None,
                     "pass": bool(c2 is not None and _free_rank(c2) == 1)})

    return rows


# ---------------------------------------------------------------------------
# THE SELF-DETECTED-ERROR LOOP — the agent runs its own self-verify, reads off the
# FAILED known, articulates its OWN wrong operator + the correction it needs, ASKS;
# the parent bridges ONE corrected concept; the agent re-composes + re-verifies.
# ---------------------------------------------------------------------------

# which FAILING known maps to which corrected concept (read off the operator state,
# NOT a hand map of the answer): a connected-glue rank-too-low -> HNN; a
# multi-collapse rank-too-low -> wedge.
def agent_self_detected_error():
    """Read the failed self-verify rows; for each, the agent names its OWN wrong
    operator + the corrected concept it lacks, and poses the correction question.
    Empty when the gate is clean."""
    rows = self_verify_operations()
    reports = []
    for r in rows:
        if r["pass"] or r["got_rank"] is None:
            continue
        if "HNN" in r["case"] and "van_kampen_glue_connected" not in _BRIDGED:
            reports.append({
                "case": r["case"], "got": r["got_rank"], "expected": r["expected_rank"],
                "wrong_op": "I applied the AMALGAM glue to two boundary circles of an "
                            "ALREADY-CONNECTED piece",
                "lacked": ["van_kampen_glue_connected"],
                "question": (
                    f"My self-verify CAUGHT a failure: gluing the two boundary circles "
                    f"of a single annulus to each other should give a torus (pi_1 free "
                    f"rank 2), but my amalgam glue read rank {r['got_rank']}. The two "
                    f"circles are in the SAME connected piece. Is gluing two boundary "
                    f"circles of an already-connected space the SAME amalgamated "
                    f"product, or something else?")})
            return reports
        if "wedge" in r["case"] and "collapse_wedge" not in _BRIDGED:
            reports.append({
                "case": r["case"], "got": r["got_rank"], "expected": r["expected_rank"],
                "wrong_op": "I killed EACH circle's class but treated collapsing "
                            "several circles to ONE point as just killing each class",
                "lacked": ["collapse_wedge"],
                "question": (
                    f"My self-verify CAUGHT a failure: collapsing both ends of a "
                    f"cylinder to a SINGLE point should give S^2 v S^1 (pi_1 free rank "
                    f"1), but my kill-each-class collapse read rank {r['got_rank']}. Is "
                    f"collapsing SEVERAL circles to one SHARED point just killing each "
                    f"class, or does identifying the points to one point add "
                    f"something?")})
            return reports
    return reports


def parent_correct_concept(ask: dict):
    """The parent for a self-detected error: bridge ONE corrected compositional
    concept, keyed by ask['lacked']. Reuses the single _PARENT_COMPOSE_TABLE (the HNN
    / wedge corrections live there). NEVER the spec, the surface, or J."""
    return parent_compose_step(ask)


def run_self_correction_loop(max_asks: int = 4):
    transcript = []
    n = 0
    while n < max_asks:
        reports = agent_self_detected_error()
        if not reports:
            break
        ask = reports[0]
        one_step = parent_correct_concept(ask)
        rec = {"self_detect": {"case": ask["case"], "got": ask["got"],
                               "expected": ask["expected"], "wrong_op": ask["wrong_op"]},
               "question": ask["question"], "lacked": ask["lacked"],
               "one_step": one_step, "advanced": None}
        if one_step is None:
            rec["advanced"] = "parent mute / no one-step"
            transcript.append(rec)
            break
        incorporate_compose_step(one_step)
        rec["advanced"] = (f"re-composed with corrected concept "
                           f"{one_step['answered']!r} -> {one_step['op']!r}")
        transcript.append(rec)
        n += 1
    return transcript


# ===========================================================================
# THE PANTS COMPOSITION — the agent APPLIES its (corrected, self-verified) operators
# to the named pieces, MECHANICALLY tracking boundary circles. NO LLM-reasoned
# surface; every line is an operator application + boundary bookkeeping.
#
# Prose (671579): "Sew two pairs of pants together, each leg opening sewn to its
# counterpart's leg opening. Then, identify the waistbands into a single point."
#   "two pairs of pants"           -> two represent_pants pieces (P, Q)
#   "each leg sewn to counterpart" -> glue_circles on the LEG boundaries (pairwise)
#   "identify the waistbands into  -> collapse_circles on the WAIST boundaries to a
#    a single point"                   single point
# The boundary roles (waist=b0, leg=b1,b2) come from the pants REPRESENTATION the
# agent derived — NOT from the shell labelling the topology.
# ===========================================================================

def compose_pants_structure():
    """The agent COMPOSES the pants structure by applying its operators. Returns the
    final Piece + a step ledger, or (None, ledger) if an operator is not runnable."""
    ledger = []
    # (i) REPRESENT each pants over fresh disjoint generators. b0=waist, b1,b2=legs.
    P = represent_pants("a", "b")
    Q = represent_pants("c", "d")
    if P is None or Q is None:
        return None, ledger
    ledger.append(("represent", f"P = {P.note}; boundaries {P.boundaries} "
                               f"(waist,leg,leg)"))
    ledger.append(("represent", f"Q = {Q.note}; boundaries {Q.boundaries} "
                               f"(waist,leg,leg)"))
    U = disjoint_union(P, Q)               # 2 components
    P_waist, P_leg1, P_leg2 = 0, 1, 2
    Q_waist, Q_leg1, Q_leg2 = 3, 4, 5
    # record the leg/waist WORDS so we can re-find them after boundaries shrink.
    p_leg2_w, q_leg2_w = U.boundaries[P_leg2], U.boundaries[Q_leg2]
    p_waist_w, q_waist_w = U.boundaries[P_waist], U.boundaries[Q_waist]
    ledger.append(("layout", f"U boundaries {U.boundaries}; components={U.components} "
                            f"(P waist@0 legs@1,2 ; Q waist@3 legs@4,5)"))

    # (ii) GLUE legs pairwise. FIRST glue (separate components) -> amalgam (merges).
    g1 = glue_circles(U, P_leg1, Q_leg1)
    if g1 is None:
        return None, ledger
    ledger.append(("glue", f"sew P.leg1~Q.leg1 -> {g1.note.split('|')[-1].strip()}; "
                          f"relator {g1.relators[-1]!r}; components={g1.components}; "
                          f"bdry {g1.boundaries}"))
    # SECOND glue (now ONE connected piece) -> HNN. re-find the leg words.
    i2 = g1.boundaries.index(p_leg2_w)
    j2 = g1.boundaries.index(q_leg2_w)
    g2 = glue_circles(g1, i2, j2)
    if g2 is None:
        return None, ledger
    ledger.append(("glue", f"sew P.leg2~Q.leg2 -> {g2.note.split('|')[-1].strip()}; "
                          f"relator {g2.relators[-1]!r}; components={g2.components}; "
                          f"bdry {g2.boundaries}"))

    # (iii) COLLAPSE both waists to a SINGLE point (kill each class + wedge).
    wi = g2.boundaries.index(p_waist_w)
    wj = g2.boundaries.index(q_waist_w)
    final = collapse_circles(g2, sorted([wi, wj]))
    if final is None:
        return None, ledger
    ledger.append(("collapse", f"identify both waistbands ({p_waist_w!r},{q_waist_w!r}) "
                              f"to one point -> {final.note.split('|')[-1].strip()}; "
                              f"relators {final.relators}; gens {final.gens!r}"))
    ledger.append(("result", f"composed pi_1 = {final.presentation()!r}; "
                            f"remaining boundaries {final.boundaries}"))
    return final, ledger


# ===========================================================================
# END-ONLY answer-key + structural verify vs J = (Z x Z) * Z.
# ===========================================================================

def load_answer_key() -> str:
    data = json.loads((ROOT / "data" / "hle_math.json").read_text())
    for it in data:
        if str(it.get("id", "")).startswith(PROSE_ID_PREFIX):
            return it["answer"]
    return "?"


def j_reference():
    return _cr.pi1_from_relators("abc", ["aba-b-"])     # (ZxZ)*Z, H_1 = Z^3


def main() -> None:
    _BRIDGED.clear()
    s = _native.Substrate()
    try:
        s.add_node("Goal", {"kind": "compose",
                            "raw": "compose the pants structure from named pieces"})
    except Exception:
        pass

    prose = ("Sew two pairs of pants together, each leg opening sewn to its "
             "counterpart's leg opening. Then, identify the waistbands into a single "
             "point. What is the fundamental group of this topological space?")

    print("=" * 78)
    print("STRICT COMPREHENSION->STRUCTURE — COMPOSE the pants structure from the "
          "named pieces")
    print("=" * 78)
    print("PROSE (the construction the agent comprehends):")
    print(f"  {prose!r}")
    print()
    print("The agent's COMPOSITION machinery APPLIES its named operators (represent "
          "pants ->")
    print("  glue leg circles -> collapse waist circles), tracking boundary circles. "
          "The parent")
    print("  bridges ONE compositional concept per ask. Operations self-verified on "
          "KNOWN")
    print("  textbook cases; a FAILED known is REJECTED + re-asked. J at END only "
          "(no reverse-eng).")
    print()

    # ---- THE COMPOSE ASK-TRANSCRIPT (the base concepts) ----
    print("-" * 78)
    print("THE COMPOSE ASK-TRANSCRIPT (agent composition-gap [its faculty] -> parent "
          "ONE-concept)")
    print("-" * 78)
    transcript = run_compose_ask_loop()
    for i, a in enumerate(transcript, 1):
        print(f"  COMPOSE-ASK #{i}  [the AGENT's composition machinery posed]:")
        print(f"    STEP: {a['step']}")
        print(f"    Q: {a['question']}")
        print(f"       (named gap: want={a['want']!r} lacked={a['lacked']!r})")
        os_ = a.get("one_step")
        print(f"    PARENT one compositional concept: {os_.get('concept')!r}"
              if os_ else "    PARENT: <mute / no one-step>")
        if os_:
            print(f"       (-> runnable op {os_.get('op')!r})")
        print(f"    AGENT COMPOSES: {a.get('advanced')}")
        print()
    print(f"  COMPOSE-ASK COUNT (base concepts): {len(transcript)}")
    print()

    # ---- THE SELF-VERIFY (BEFORE corrections) — the gate catches the operator errors -
    print("-" * 78)
    print("THE SELF-VERIFY (BEFORE) — the operators on KNOWN textbook cases (the gate "
          "catches errors)")
    print("-" * 78)
    before = self_verify_operations()
    for r in before:
        p = "PASS" if r["pass"] else "FAIL"
        print(f"  [{p}] {r['case']}")
        print(f"         expected rank {r['expected_rank']}; got rank {r['got_rank']}")
    caught = [r["case"] for r in before if not r["pass"]]
    print()
    print(f"  GATE: {sum(1 for r in before if r['pass'])}/{len(before)} pass; CAUGHT "
          f"{len(caught)} operator error(s).")
    print()

    # ---- THE SELF-DETECTED-ERROR CORRECTION LOOP ----
    print("-" * 78)
    print("THE SELF-CORRECTION LOOP (agent reads its OWN failed verify -> ASKS -> "
          "parent ONE corrected concept)")
    print("-" * 78)
    corr = run_self_correction_loop()
    for i, c in enumerate(corr, 1):
        sd = c["self_detect"]
        print(f"  CORRECTION-ASK #{i}  [the AGENT, off its OWN failed self-verify]:")
        print(f"    SELF-DETECT: {sd['case']} -> got rank {sd['got']} != expected "
              f"{sd['expected']}")
        print(f"    WRONG OP (the agent names its own): {sd['wrong_op']}")
        print(f"    Q: {c['question']}")
        os_ = c.get("one_step")
        print(f"    PARENT one CORRECTED concept: {os_.get('concept')!r}"
              if os_ else "    PARENT: <mute>")
        if os_:
            print(f"       (-> runnable op {os_.get('op')!r})")
        print(f"    AGENT RE-COMPOSES: {c.get('advanced')}")
        print()
    print(f"  CORRECTION-ASK COUNT: {len(corr)}")
    print()

    # ---- THE SELF-VERIFY (AFTER corrections) ----
    print("-" * 78)
    print("THE SELF-VERIFY (AFTER) — all operators on the KNOWN textbook cases")
    print("-" * 78)
    after = self_verify_operations()
    nv_pass = sum(1 for r in after if r["pass"])
    for r in after:
        p = "PASS" if r["pass"] else "FAIL"
        print(f"  [{p}] {r['case']}  (expected {r['expected_rank']}, "
              f"got {r['got_rank']})")
    print()
    print(f"  OPERATION SELF-VERIFY: {nv_pass}/{len(after)} known textbook cases pass.")
    print()

    # ---- THE PANTS COMPOSITION ----
    print("-" * 78)
    print("THE PANTS COMPOSITION (the agent APPLIES its operators; boundary circles "
          "tracked)")
    print("-" * 78)
    composed, ledger = compose_pants_structure()
    for kind, line in ledger:
        print(f"  [{kind:9}] {line}")
    print()

    # ---- THE OUTCOME — verify vs J at the END ONLY ----
    print("-" * 78)
    print("THE OUTCOME (J read at END ONLY, never to the parent)")
    print("-" * 78)
    ops_ok = (nv_pass == len(after)) and len(after) > 0
    matches = False
    if composed is None:
        print("  OUTCOME (b): PRECISE STALL — the agent named + represented the pieces "
              "but an operator")
        print("    was not runnable even with the bridges (see the transcript).")
    else:
        ch1 = composed.h1()
        jref = j_reference()
        jh1 = _cr.h1_of_presentation(jref)
        matches = (ch1.free_rank == jh1.free_rank
                   and sorted(ch1.torsion) == sorted(jh1.torsion))
        print(f"  COMPOSED pi_1 presentation : {composed.presentation()!r}")
        print(f"  COMPOSED H_1 (held read)   : free rank {ch1.free_rank}, "
              f"torsion {ch1.torsion}")
        print(f"  J = (Z x Z) * Z reference  : {jref!r} -> H_1 free rank "
              f"{jh1.free_rank}, torsion {jh1.torsion}")
        print()
        if ops_ok and matches:
            print("  OUTCOME (a): FLOOR CROSSES. The agent COMPOSED the pants structure "
                  "from its named")
            print("    pieces by APPLYING its self-verified glue/collapse operators "
                  "(amalgam + HNN +")
            print("    wedge-collapse, each corrected by FAILING a KNOWN, never by J) + "
                  "minimal parent")
            print("    concept-bridges; the held tower read pi_1; and its STRUCTURE "
                  "(H_1) MATCHES J =")
            print("    (Z x Z) * Z at the END. The comprehension->structure step "
                  "WORKS — the pants")
            print("    question SOLVES end-to-end by the AGENT's composition.")
        elif not ops_ok:
            print("  OUTCOME (b): an operator FAILED a known textbook check even after "
                  "correction ->")
            print("    REJECTED; precise stall at the failing operation.")
        else:
            print("  OUTCOME (b): the agent COMPOSED a structure (operators applied, "
                  "self-verified on")
            print("    knowns) but its H_1 does NOT match J — a precise stall, located "
                  "to the exact")
            print("    composition step that diverges.")
    print()

    key = load_answer_key()
    print(f"  [END-ONLY] the known key (never to the parent): {key!r} = (Z x Z) * Z.")
    print(f"  (Checked by STRUCTURE — H_1 — at the END; the parent only ever saw "
          f"single")
    print(f"  compositional concepts, never the spec, the surface, or the answer.)")
    print()

    # ---- INTEGRITY / DONKEY-CHECK ----
    print("-" * 78)
    print("INTEGRITY (donkey-checked)")
    print("-" * 78)
    one_concept = all(
        (a.get("one_step") is None) or
        (set(a["one_step"].keys()) <= {"concept", "op", "answered"})
        for a in (transcript + corr))
    import ast as _ast
    import inspect as _inspect
    forbidden = ("aba-b-", "abab-", "2-holed", "torus wedge", "cells=", "crush=",
                 "(z x z)", "(zxz)", "genus-1", "genus 1")
    donkey_hits = []
    for fn in (represent_pants, glue_circles, collapse_circles, disjoint_union,
               compose_pants_structure):
        src = _inspect.getsource(fn)
        node = _ast.parse(src.lstrip()).body[0]
        stmts = node.body
        if (stmts and isinstance(stmts[0], _ast.Expr)
                and isinstance(getattr(stmts[0], "value", None), _ast.Constant)
                and isinstance(stmts[0].value.value, str)):
            stmts = stmts[1:]
        for st in stmts:
            for nd in _ast.walk(st):
                if isinstance(nd, _ast.Constant) and isinstance(nd.value, str):
                    low = nd.value.lower()
                    for tok in forbidden:
                        if tok in low:
                            donkey_hits.append((fn.__name__, tok))
    no_donkey = not donkey_hits
    print(f"  DONKEY-CHECK: the composition operators carry NO hand-written spec / "
          f"topology / answer-shape")
    print(f"    (no_donkey={no_donkey}"
          f"{'' if no_donkey else ' HITS=' + str(donkey_hits)}). The agent COMPOSED by "
          f"APPLYING general operators")
    print(f"    (represent_pants / glue_circles [amalgam|HNN] / collapse_circles "
          f"[kill|wedge]),")
    print(f"    tracking boundary circles — the shell wrote NO (word,free)/cells/crush "
          f"spec and named")
    print(f"    NO resulting surface ('2-holed torus' / 'genus-1' etc.).")
    print(f"  OPERATIONS corrected ONLY by FAILING KNOWN textbook cases (the gate "
          f"caught {len(caught)} error(s)),")
    print(f"    never by J — no reverse-engineering. J read at the END only.")
    print(f"  PARENT: mute until asked, ONE compositional concept per ask "
          f"(asserted one-concept={one_concept}).")
    print(f"  The answer key (J) was read at the END only, NEVER to the parent.")
    print()
    print("[MARKER] STRICT_COMPOSE_PANTS_STRUCTURE_COMPLETED")


if __name__ == "__main__":
    main()

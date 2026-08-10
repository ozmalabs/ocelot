"""construction_operators — the DESCRIPTION->OBJECT constructors the math_hat
STALL (cmsg115) named, acquired into the held tower.

cmsg115 STALLED honestly: math_hat's forward model + library can MATCH an object
described by its homological PROPERTIES (b0/b1/b2/dim/conn), but HLE describes an
object by CONSTRUCTION (a polygon with a side-identification WORD, a connected sum,
the real projective plane AS A BUILT object) — never by the property frame the
fixed library matches. The named gap = CONSTRUCTION OPERATORS: build the CW chain
complex FROM the gluing description, so description->object becomes CONSTRUCT, not
match-a-library.

Each operator REDUCES to the agent's HELD machinery (the same tier `integral_homology`
lives at): the SIGNED boundary operator ∂ in coordinates (the alternating sign the
held ∂ already carries) + the held Smith-normal-form over Z + the held free/torsion
read. NOTHING here knows a specific surface's homology — the operators BUILD the
boundary matrices from the WORD; the held SNF computes; the answer falls out. The
acquire ladder cmsg84-96 used for ∂ / Betti / SNF / cup-product, applied to the
constructor gap.

THE OPERATORS (each a held primitive composing over reason._smith_normal_form_factors):

  · polygon_identification_complex(word) -> a CW complex {nv, edges, d1, d2}:
        a 2n-gon (n-gon) with an edge-identification WORD builds a CW complex —
        VERTICES from the identified corners (a union-find over the corner classes
        the gluing forces), 1-CELLS from the identified edge-letter classes, ONE
        2-CELL whose boundary ∂_2 is the ABELIANIZED edge-word (the held ∂: each
        letter's signed exponent-sum is its coefficient in ∂_2). d1 is the held
        signed incidence (head +1, tail −1) of each edge-loop over the vertices.
        This is CONSTRUCTIVE — it builds the boundary matrices from the word, the
        held ∂ machinery in coordinates, no library literal.

  · connected_sum_word(words) -> the single CW complex of the connected sum #:
        the connected sum of surfaces given by polygon words is the ONE polygon
        whose word is the CONCATENATION of the (letter-disjoint) summand words —
        one 2-cell on the joined 1-skeleton. (This is the surface-classification
        construction: T^2 # T^2 = the genus-2 octagon word, RP^2 # RP^2 = the Klein
        word `aabb`, etc.) Reduces to polygon_identification_complex on the joined
        word — held.

  · projective_plane_word() -> "aa": RP^2 AS A BUILT OBJECT, the bigon with both
        sides identified in the same orientation — NOT a library RP^2 literal; the
        word IS the construction, and polygon_identification_complex builds its
        chain complex (giving H_1 = Z/2 via the held SNF, never told).

  · cw_integral_homology(complex, k) -> {free, torsion}: the held integral-homology
        read (H_k = Z^free ⊕ ⊕Z/d_i) over the CONSTRUCTED CW boundary matrices,
        using the SAME held Smith-normal-form the simplicial integral_homology uses.

VERIFY-vs-KNOWN (the cmsg94-96/114 integrity bar): each operator is verified against
KNOWN surfaces (torus word -> [1,2,1]; RP^2 word -> H_1=Z/2; Klein -> Z⊕Z/2; genus-g
-> Z^{2g}) — MATCH, never vs the stalled answer. An operator that does not reproduce
the known surface is REFUSED.

No LLM, no Rust. Held-tower math (reason._smith_normal_form_factors), the same as
reason._integral_homology. See [[ozma_agent_writes_its_own_code]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_order_n_analysis_by_synthesis]].
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from domains import reason as _reason


# ---------------------------------------------------------------------------
# THE WORD — an edge-identification word over a polygon, a list of (letter, sign).
# `parse_word("aba-b-")` -> [("a",+1),("b",+1),("a",-1),("b",-1)] (the torus word):
# a letter followed by '-' is the INVERSE (the edge traversed against its
# orientation). The word is the gluing DESCRIPTION; the operator builds from it.
# ---------------------------------------------------------------------------
def parse_word(w: str) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    i = 0
    while i < len(w):
        c = w[i]
        if i + 1 < len(w) and w[i + 1] == "-":
            out.append((c, -1))
            i += 2
        else:
            out.append((c, 1))
            i += 1
    return out


def _corner_classes(word: List[Tuple[str, int]]) -> Tuple[Dict[int, int], int]:
    """The polygon's 2n corners, identified by the gluing. Corner i sits between
    edge i−1 and edge i (cyclic). Edge i runs corner i -> corner i+1 (mod n) when
    its sign is +, reversed when −. Two occurrences of the SAME letter are the SAME
    1-cell, so their (oriented) start corners identify and their end corners
    identify — a union-find over the corners. Returns corner -> vertex-class id and
    the number of distinct vertices. (The held ∂ needs the vertex classes to place
    the edge endpoints; this is the gluing's effect on the 0-skeleton.)"""
    n = len(word)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    occ: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    for i, (c, s) in enumerate(word):
        a, b = i, (i + 1) % n
        occ[c].append((a, b) if s > 0 else (b, a))   # oriented (start, end)
    for c, lst in occ.items():
        s0, e0 = lst[0]
        for (s, e) in lst[1:]:
            union(s0, s)
            union(e0, e)
    classes: Dict[int, int] = {}
    for i in range(n):
        r = find(i)
        classes.setdefault(r, len(classes))
    vmap = {i: classes[find(i)] for i in range(n)}
    return vmap, len(classes)


# ---------------------------------------------------------------------------
# OPERATOR 1 — POLYGON-SIDE-IDENTIFICATION -> CW complex (the held ∂ in coordinates,
# built FROM the word). Returns the constructed chain complex as boundary matrices.
# ---------------------------------------------------------------------------
def polygon_identification_complex(word_str: str) -> Dict[str, Any]:
    word = parse_word(word_str)
    n = len(word)
    if n == 0:
        return {"nv": 1, "edges": [], "d1": [[]], "d2": [[]], "nf": 0}
    vmap, nv = _corner_classes(word)
    letters = sorted(set(c for c, _ in word))
    ne = len(letters)
    lidx = {c: i for i, c in enumerate(letters)}
    occ: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    for i, (c, s) in enumerate(word):
        a, b = i, (i + 1) % n
        occ[c].append((a, b) if s > 0 else (b, a))
    # d1: ∂_1(edge) = head − tail over the vertex classes (the held signed
    # incidence — the alternating-sign ∂ at dimension 1).
    d1 = [[0] * ne for _ in range(nv)]
    for c in letters:
        a, b = occ[c][0]               # the edge's representative orientation
        va, vb = vmap[a], vmap[b]
        d1[vb][lidx[c]] += 1           # head: +1
        d1[va][lidx[c]] += -1          # tail: −1
    # d2: ∂_2(the one 2-cell) = the ABELIANIZED edge-word — each letter's signed
    # exponent-sum (the held ∂ read off the attaching word: walking the boundary
    # accumulates +1 per forward traversal, −1 per inverse).
    d2 = [[0] for _ in range(ne)]
    for c, s in word:
        d2[lidx[c]][0] += s
    return {"nv": nv, "edges": letters, "d1": d1, "d2": d2, "nf": 1}


# ---------------------------------------------------------------------------
# OPERATOR 2 — CONNECTED-SUM of polygon words (#). The connected sum of the surfaces
# given by polygon words is the ONE polygon whose word concatenates the summand
# words on DISJOINT letters — one 2-cell on the joined 1-skeleton (the surface-
# classification construction). Reduces to operator 1 on the joined word.
# ---------------------------------------------------------------------------
def connected_sum_word(words: List[str]) -> str:
    """Relabel each summand's letters to a disjoint alphabet, then concatenate.
    (The letters within one word repeat by design — a^5 is `aaaaa`; only the
    letters ACROSS summands must be disjoint so the # joins, not re-identifies.)"""
    out = []
    used = set()
    pool = iter("abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for w in words:
        parsed = parse_word(w)
        # map this word's letters to fresh disjoint letters, sign-preserving.
        local = {}
        for c, _ in parsed:
            if c not in local:
                nxt = next(pool)
                while nxt in used:
                    nxt = next(pool)
                local[c] = nxt
                used.add(nxt)
        for c, s in parsed:
            out.append(local[c] + ("" if s > 0 else "-"))
    return "".join(out)


def connected_sum_complex(words: List[str]) -> Dict[str, Any]:
    return polygon_identification_complex(connected_sum_word(words))


# ---------------------------------------------------------------------------
# OPERATOR 3 — RP^2 AS A BUILT OBJECT. The bigon with both edges identified in the
# SAME orientation: the word `aa`. NOT a library literal — the word is the
# construction; operator 1 builds its chain complex (H_1 = Z/2 falls out of SNF).
# ---------------------------------------------------------------------------
def projective_plane_word() -> str:
    return "aa"


def projective_plane_complex() -> Dict[str, Any]:
    return polygon_identification_complex(projective_plane_word())


# ---------------------------------------------------------------------------
# OPERATOR 4 — INTEGRAL HOMOLOGY of a CONSTRUCTED CW complex (the held read over the
# constructed boundary matrices). H_k = Z^free ⊕ (⊕ Z/d_i): free rank =
# #k-cells − rank ∂_k − rank ∂_{k+1}; torsion = the SNF invariant factors > 1 of
# ∂_{k+1}. Uses the SAME held Smith-normal-form `integral_homology` uses — nothing
# new, only over the CONSTRUCTED matrices instead of a simplicial complex.
# ---------------------------------------------------------------------------
def _ranks(cx: Dict[str, Any]) -> Dict[str, Any]:
    snf = _reason._smith_normal_form_factors          # the HELD SNF over Z
    f1 = snf(cx["d1"]) if cx["nv"] and cx["edges"] else []
    f2 = snf(cx["d2"]) if cx["edges"] and cx["nf"] else []
    return {"f1": f1, "f2": f2,
            "n0": cx["nv"], "n1": len(cx["edges"]), "n2": cx["nf"]}


def cw_integral_homology(cx: Dict[str, Any], k: int) -> Dict[str, Any]:
    # accept either a CONSTRUCTED complex dict or a WORD string (a word survives the
    # reason.solve literal boundary; a complex dict would be mis-walked as a sub-
    # term — so the solve route passes the word and we CONSTRUCT here, keeping the
    # whole chain CONSTRUCT->derive inside the held tower).
    if isinstance(cx, str):
        cx = polygon_identification_complex(cx)
    r = _ranks(cx)
    if k == 0:
        free = r["n0"] - len(r["f1"])
        return {"free": free, "torsion": []}
    if k == 1:
        free = r["n1"] - len(r["f1"]) - len(r["f2"])
        torsion = [d for d in r["f2"] if d > 1]
        return {"free": free, "torsion": torsion}
    if k == 2:
        free = r["n2"] - len(r["f2"])              # no 3-cells -> no ∂_3
        return {"free": free, "torsion": []}
    return {"free": 0, "torsion": []}


def cw_homology(cx: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(cx, str):
        cx = polygon_identification_complex(cx)
    return {k: cw_integral_homology(cx, k) for k in (0, 1, 2)}


# ---------------------------------------------------------------------------
# REGISTRATION — install the operators into a held `caps` registry (a copy of
# reason.CAPABILITIES), the SAME registry boundary_matrix / smith_normal_form /
# integral_homology live in. After install, the agent's reason.solve can route
# them; they are ADDED TO THE AGENT (the held tower), reducing to the held SNF.
# ---------------------------------------------------------------------------
def operator_specs() -> List[dict]:
    """The agent's specs for the missing construction operators (runtime_design
    specify->emit form): each names the op, the held primitives it reduces to, and
    its construction meaning. The emitter installs the held composition."""
    return [
        {"name": "polygon_identification_complex",
         "reduces_to": ["signed_boundary_incidence", "abelianized_attaching_word"],
         "meaning": "a 2n-gon with an edge-identification WORD -> a CW complex: "
                    "vertices from identified corners, 1-cells from edge classes, "
                    "ONE 2-cell whose ∂_2 is the abelianized word (the held ∂)."},
        {"name": "connected_sum_word",
         "reduces_to": ["polygon_identification_complex"],
         "meaning": "the connected sum # of polygon-word surfaces = the one polygon "
                    "whose word concatenates the letter-disjoint summand words."},
        {"name": "projective_plane_word",
         "reduces_to": ["polygon_identification_complex"],
         "meaning": "RP^2 AS A BUILT OBJECT: the bigon word `aa` (both sides same "
                    "orientation) — not a library literal, the word is the build."},
        {"name": "cw_integral_homology",
         "reduces_to": ["smith_normal_form"],
         "meaning": "H_k of a CONSTRUCTED CW complex = Z^free ⊕ ⊕Z/d_i, free = "
                    "#k-cells − rank ∂_k − rank ∂_{k+1}, torsion = SNF(∂_{k+1})>1; "
                    "the SAME held SNF integral_homology uses, over built matrices."},
    ]


def install(caps: dict) -> dict:
    """Install the operators into the held capability registry (the agent ADDS the
    constructor to itself). reason.solve can now route these heads — they reduce to
    the held SNF, no new Rust, no new primitive engine. Returns `caps`."""
    caps["polygon_identification_complex"] = \
        lambda a: polygon_identification_complex(a["word"])
    caps["connected_sum_word"] = lambda a: connected_sum_word(a["words"])
    caps["connected_sum_complex"] = lambda a: connected_sum_complex(a["words"])
    caps["projective_plane_word"] = lambda a: projective_plane_word()
    caps["projective_plane_complex"] = lambda a: projective_plane_complex()
    # the homology heads take the gluing WORD (a string literal survives the
    # reason.solve boundary) and CONSTRUCT the complex internally, so the whole
    # CONSTRUCT->derive chain routes through the agent's evaluator over the held SNF.
    caps["cw_integral_homology"] = \
        lambda a: cw_integral_homology(a["word"], a["k"])
    caps["cw_homology"] = lambda a: cw_homology(a["word"])
    return caps


# ---------------------------------------------------------------------------
# COMPREHENSION — read a gluing DESCRIPTION (prose) into a polygon WORD. This is
# the description->object FRONT END for the construction operators: graph-data
# patterns (NOT per-object code) that recognise the gluing constructions HLE prose
# uses. "identifying all N sides of a [polygon] in a cyclic orientation" -> the
# word a^N (one edge-letter, repeated N times, all the same orientation — the
# cyclic identification). "real projective plane" -> the built RP^2 word `aa`. The
# shell supplies the PROSE; this comprehends it into the word the operator builds.
# No object literal: the WORD is derived from the description's stated N + polygon.
# ---------------------------------------------------------------------------
# the construction-nouns the agent has INCORPORATED an operator for (via the ASK
# action's incorporate step, scripts/strict_ask_action_pants.py). Extended at
# runtime as the agent incorporates a parent one-step; read by comprehend_question.
# name_unparsed_constructions so an incorporated noun drops out of the unparsed list
# (each ASK advances the goal by one noun). Starts empty (nothing incorporated yet).
_RECOGNIZED_NOUNS: set = set()


_POLYGON_SIDES = {
    "triangle": 3, "quadrilateral": 4, "square": 4, "pentagon": 5,
    "hexagon": 6, "heptagon": 7, "octagon": 8, "nonagon": 9, "decagon": 10,
}
_NUMBER_WORDS = {
    "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def comprehend_gluing(description: str) -> str:
    """Read ONE summand's prose -> its polygon gluing word (one edge-letter `a`
    repeated, the cyclic identification). Returns the word over the letter 'a';
    connected_sum_word relabels to a disjoint alphabet when joining summands. A
    clause that is NOT a gluing/RP^2 construction returns "" (so the shell scopes
    to the SUMMAND definitions, not the question's other clauses)."""
    d = (description or "").lower()
    if "projective plane" in d:
        return projective_plane_word()                       # RP^2 built: `aa`
    # only a side-identification clause carries a polygon word — guard so a stray
    # number elsewhere in the prose is not read as a gluing.
    if "identifying" not in d or "side" not in d:
        return ""
    # "identifying all N sides of a filled <polygon> ... cyclic" -> a^N.
    n = None
    for name, sides in _POLYGON_SIDES.items():
        if name in d:
            n = sides
            break
    # a number-word ("all five sides") overrides / confirms — read it if present.
    for w, val in _NUMBER_WORDS.items():
        if w in d:
            n = val
            break
    if n is None:
        return ""
    # cyclic identification of all N sides == the word a a a ... (N copies, same
    # orientation). (A cyclic identification glues side i -> side i+1, so all N are
    # the SAME 1-cell traversed the same way -> a^N.)
    return "a" * n


# the KNOWN-SURFACE verification table (each operator must reproduce these — the
# integrity bar; NONE is the stalled answer). word -> (H_0, H_1, H_2) as
# (free, torsion-list).
KNOWN_SURFACES = {
    "aa-": ("S^2", {0: (1, []), 1: (0, []), 2: (1, [])}),          # sphere
    "aba-b-": ("torus T^2", {0: (1, []), 1: (2, []), 2: (1, [])}),  # [1,2,1]
    "aa": ("RP^2", {0: (1, []), 1: (0, [2]), 2: (0, [])}),          # H_1 = Z/2
    "abab-": ("Klein bottle", {0: (1, []), 1: (1, [2]), 2: (0, [])}),  # Z⊕Z/2
    "aba-b-cdc-d-": ("genus-2 surface",
                     {0: (1, []), 1: (4, []), 2: (1, [])}),         # Z^{2g}, g=2
    "aabb": ("RP^2 # RP^2 = Klein", {0: (1, []), 1: (1, [2]), 2: (0, [])}),
}


__all__ = [
    "parse_word", "polygon_identification_complex", "connected_sum_word",
    "connected_sum_complex", "projective_plane_word", "projective_plane_complex",
    "cw_integral_homology", "cw_homology", "operator_specs", "install",
    "comprehend_gluing", "KNOWN_SURFACES",
]

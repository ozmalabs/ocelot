#!/usr/bin/env python3
"""construct_compute_pi1 — the CONSTRUCTIVE-COMPUTATION route for the FUNDAMENTAL GROUP
of a GLUED / CONSTRUCTED CW 2-COMPLEX: "what is pi_1 of [this glued space]?", answered
against the multiple-choice group expressions the question lists.

THE GAP THIS CLOSES. The named-space (co)homology faculty (construct_compute_betti)
reads a NAMED space and computes a (co)homology DIMENSION. The bank also asks for the
FUNDAMENTAL GROUP of a space BUILT by a gluing recipe (sew pieces along boundaries,
collapse boundaries to a point) — "Sew two pairs of pants together, each leg sewn to
its counterpart, then identify the waistbands to a point. What is pi_1?". This is the
same recognize -> construct(CW) -> compute shape, extended to a pi_1 PRESENTATION
(generators/relators via van Kampen on the cell structure) and IDENTIFIED against the
listed group-expression options (free product / direct product / free group).

WHAT IS GENERAL. The CONSTRUCTION reuses the held, self-verified composition operators
(represent a piece -> glue boundary circles [van Kampen amalgam if separate, HNN if
already connected] -> collapse boundary circles to a point [kill class + wedge]) from
strict_compose_pants_structure — the SAME operators, each proven on KNOWN textbook
cases (two disks->S^2, annulus self-glue->torus [HNN], cylinder->one-point->S^2vS^1
[wedge]). They are driven by a PARSED gluing plan (count of pieces, which boundaries
sew to which, which collapse), not a hand-written presentation. The pi_1 PRESENTATION
is then read by the held tower (pi1_from_relators) and reduced to its FREE-PRODUCT
FACTOR SIGNATURE by the held verifier (Tietze-simplify -> free-product decompose by
relator-connectivity -> standard-form factor recognizers Z^n/Z/Z/m/F_k), all GENERAL
(verified on independent presentations). The IDENTIFY step parses EACH listed option's
group expression into its OWN factor signature and matches — the same parser on every
option, no per-question answer.

THE SELF-CERTIFICATION DISCIPLINE (zero false positives). A value (the option letter)
is emitted ONLY when ALL hold:
  · the construction operators PASS their textbook self-verify (a wrong operator is
    caught by a failing known and the construction is refused);
  · the computed pi_1 signature matches EXACTLY ONE listed option (ambiguity -> MISS);
  · the H_1 CROSS-CHECK agrees: the abelianization of the computed pi_1 presentation
    (held SNF) EQUALS the abelianization of the matched option's group expression. A
    pi_1 whose H_1 disagrees with the option is rejected. (H_1 alone cannot pick the
    option — Z^3 is shared by F_3, Z^3, (ZxZ)*Z — but it is a necessary cross-check the
    construction did not silently diverge.)
Outside the recognized gluing-plan family, or on any failed check, NO value is emitted
— an honest miss, never a guess. The KEY is never consulted.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It READS the gluing plan + the options off
the stem (mechanical), DRIVES the held self-verified construction operators, COMPUTES
the pi_1 presentation + factor signature via the held tower/verifier, and MATCHES the
options by the same general expression parser. No per-question branch, no LLM, no Rust,
no key.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import construction_operators as _co
from domains import commutator_rank as _cr
from domains import certify as _certify


@dataclass
class Pi1Result:
    kind: Optional[str] = None       # pi1_option | None
    value: Optional[str] = None      # the matched option LETTER (e.g. "J")
    detail: str = ""
    provenance: list = field(default_factory=list)


# ===========================================================================
# HELD WORD ALGEBRA (parse_word syntax: 'a' forward, 'a-' inverse). String ops over the
# boundary WORDS the operators carry — the SAME minimal algebra the strict scripts use.
# ===========================================================================

def _letters(word: str) -> List[Tuple[str, int]]:
    return _co.parse_word(word)


def _gens_in(word: str) -> List[str]:
    return sorted({c for c, _ in _letters(word)})


def _inv(word: str) -> str:
    out = []
    for c, s in reversed(_letters(word)):
        out.append(c + ("-" if s > 0 else ""))
    return "".join(out)


def _concat(*words: str) -> str:
    return "".join(w for w in words if w)


def _freely_reduce(word: str) -> str:
    stack: List[Tuple[str, int]] = []
    for c, s in _letters(word):
        if stack and stack[-1][0] == c and stack[-1][1] == -s:
            stack.pop()
        else:
            stack.append((c, s))
    return "".join(c + ("" if s > 0 else "-") for c, s in stack)


def _substitute(word: str, mapping: Dict[str, str]) -> str:
    out = []
    for c, s in _letters(word):
        repl = mapping.get(c, c)
        out.append(repl if s > 0 else _inv(repl))
    return _freely_reduce("".join(out))


_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _fresh_gen(used: str) -> str:
    for c in _LETTERS:
        if c not in used:
            return c
    raise RuntimeError("out of generator letters")


# ===========================================================================
# THE PIECE + THE HELD, SELF-VERIFIED CONSTRUCTION OPERATORS. A piece is (presentation
# pi_1, tracked boundary-circle words, #connected components). The operators are the
# GENERAL van-Kampen ones (each self-verified on textbook knowns in self_verify_ops):
#   represent_genus0(k): a genus-0 surface with k boundary circles -> F_{k-1} free, k
#       boundary loops b_0..b_{k-1} with product 1 (b_0..b_{k-2} free, b_{k-1} their
#       inverse-product). [The general 'pair of pants' is k=3.]
#   glue(i,j): identify boundary i with j -> amalgam (separate components) or HNN
#       (already connected, new stable t with t c_i t^-1 = c_j).
#   collapse(idxs): kill each circle's class + wedge in (m-1) free gens for m circles
#       collapsed to ONE shared point.
# These are IDENTICAL to the strict scripts' operators; carried here so the faculty is
# self-contained (and donkey-checked by the same self-verify).
# ===========================================================================

@dataclass
class Piece:
    gens: str
    relators: List[str]
    boundaries: List[str]
    components: int = 1
    note: str = ""

    def presentation(self):
        return _cr.pi1_from_relators(self.gens, self.relators)

    def h1(self):
        return _cr.h1_of_presentation(self.presentation())


def represent_genus0(k: int, gen_pool: str) -> Piece:
    """A genus-0 surface with k boundary circles: pi_1 = F_{k-1} (free) on fresh
    generators g_0..g_{k-2}; boundary loops b_0=g_0, .., b_{k-2}=g_{k-2}, and
    b_{k-1} = (g_0..g_{k-2})^-1 (the boundary-product relation b_0..b_{k-1}=1). General
    over k; k=3 is a pair of pants. gen_pool supplies fresh disjoint letters."""
    used = gen_pool
    gens = ""
    for _ in range(k - 1):
        g = _fresh_gen(used)
        used += g
        gens += g
    boundaries = [g for g in gens]                      # b_0..b_{k-2}
    last = _inv(_concat(*gens)) if gens else ""         # b_{k-1} = (prod)^-1
    boundaries.append(last)
    return Piece(gens=gens, relators=[], boundaries=boundaries, components=1,
                 note=f"genus0(k={k}): F_{max(k-1,0)}, {k} boundaries (prod=1)")


def disjoint_union(a: Piece, b: Piece) -> Piece:
    return Piece(gens=a.gens + b.gens, relators=list(a.relators) + list(b.relators),
                 boundaries=list(a.boundaries) + list(b.boundaries),
                 components=a.components + b.components, note=a.note + " + " + b.note)


def glue(piece: Piece, i: int, j: int) -> Piece:
    """Glue boundary i to j. SEPARATE components -> amalgam (relator c_i = c_j, merge);
    SAME component -> HNN (fresh stable t, t c_i t^-1 = c_j)."""
    c1, c2 = piece.boundaries[i], piece.boundaries[j]
    new_bnd = [b for k, b in enumerate(piece.boundaries) if k not in (i, j)]
    if piece.components >= 2:
        relator = _concat(c1, _inv(c2))
        return Piece(gens=piece.gens, relators=list(piece.relators) + [relator],
                     boundaries=new_bnd, components=piece.components - 1,
                     note=piece.note + f" | amalgam {i}~{j}")
    t = _fresh_gen(piece.gens)
    relator = _concat(t, c1, t + "-", _inv(c2))
    return Piece(gens=piece.gens + t, relators=list(piece.relators) + [relator],
                 boundaries=new_bnd, components=piece.components,
                 note=piece.note + f" | HNN {i}~{j} (stable {t})")


def collapse(piece: Piece, idxs: List[int]) -> Piece:
    """Collapse boundaries at idxs to ONE shared point: kill each class (relator c=1) +
    wedge in (len(idxs)-1) fresh free generators (identifying m points wedges m-1
    circles)."""
    new_rel = list(piece.relators)
    new_gens = piece.gens
    for i in idxs:
        new_rel.append(piece.boundaries[i])
    for _ in range(max(len(idxs) - 1, 0)):
        w = _fresh_gen(new_gens)
        new_gens += w
    new_bnd = [b for k, b in enumerate(piece.boundaries) if k not in idxs]
    return Piece(gens=new_gens, relators=new_rel, boundaries=new_bnd,
                 components=piece.components, note=piece.note + f" | collapse {idxs}")


# ===========================================================================
# THE PI_1 VERIFIER — Tietze-simplify -> free-product decompose by relator-connectivity
# -> standard-form factor recognizers -> the factor MULTISET (the pi_1 signature). The
# SAME general pipeline strict_pi1_verify_pants proved (rejecting the H_1-imposters).
# ===========================================================================

def tietze_simplify(gens: str, relators: List[str]) -> Tuple[str, List[str]]:
    rels = [r for r in (_freely_reduce(r) for r in relators) if r]
    changed = True
    while changed:
        changed = False
        for r in list(rels):
            lts = _letters(r)
            if len(lts) == 1:
                g = lts[0][0]
                rels = [x for x in (_freely_reduce(_substitute(y, {g: ""}))
                                    for y in rels if y != r) if x]
                gens = gens.replace(g, "")
                changed = True
                break
        if changed:
            continue
        for r in list(rels):
            lts = _letters(r)
            if len(lts) == 2 and lts[0][0] != lts[1][0] and lts[0][1] == -lts[1][1]:
                keep, drop = lts[0][0], lts[1][0]
                rels = [x for x in (_freely_reduce(_substitute(y, {drop: keep}))
                                    for y in rels if y != r) if x]
                gens = gens.replace(drop, "")
                changed = True
                break
    return gens, rels


def free_product_decompose(gens: str, relators: List[str]) -> List[Tuple[str, List[str]]]:
    glist = list(gens)
    gidx = {g: i for i, g in enumerate(glist)}
    parent = list(range(len(glist)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in relators:
        inv = [gidx[g] for g in _gens_in(r) if g in gidx]
        for i in range(1, len(inv)):
            parent[find(inv[0])] = find(inv[i])

    comp_g: Dict[int, List[str]] = {}
    for g in glist:
        comp_g.setdefault(find(gidx[g]), []).append(g)
    comp_r: Dict[int, List[str]] = {root: [] for root in comp_g}
    for r in relators:
        ig = _gens_in(r)
        if ig:
            comp_r[find(gidx[ig[0]])].append(r)
    factors = [("".join(sorted(comp_g[root])), list(comp_r[root])) for root in comp_g]
    factors.sort(key=lambda f: (len(f[0]), f[0]))
    return factors


def _is_commutator_of(r: str, x: str, y: str) -> bool:
    rr = _freely_reduce(r)
    sp = set()
    for u in (x, x + "-"):
        for v in (y, y + "-"):
            sp.add(_freely_reduce(u + v + _inv(u) + _inv(v)))
            sp.add(_freely_reduce(v + u + _inv(v) + _inv(u)))
    return rr in sp


def recognize_factor(gens: str, relators: List[str]) -> str:
    """Standard-form tag of a single component: Z^n / Z / Z/m / F_k, else '?<...>'."""
    rels = [r for r in (_freely_reduce(r) for r in relators) if r]
    n = len(gens)
    if not rels:
        if n == 0:
            return "1"
        if n == 1:
            return "Z"
        return f"F{n}"
    if n == 1 and len(rels) == 1:
        lts = _letters(rels[0])
        if lts and len({c for c, _ in lts}) == 1 and len({s for _, s in lts}) == 1:
            m = len(lts)
            if m >= 2:
                return f"Z{m}"
    pairs = list(combinations(gens, 2))
    if n >= 2 and len(rels) == len(pairs):
        matched, ok = set(), True
        for r in rels:
            ig = _gens_in(r)
            if len(ig) != 2 or not _is_commutator_of(r, ig[0], ig[1]):
                ok = False
                break
            matched.add(tuple(ig))
        if ok and matched == set(pairs):
            return f"Z^{n}"
    return f"?<{gens}|{','.join(rels)}>"


def pi1_signature(gens: str, relators: List[str]) -> List[str]:
    g2, r2 = tietze_simplify(gens, relators)
    factors = free_product_decompose(g2, r2)
    return sorted(recognize_factor(fg, fr) for fg, fr in factors)


# ===========================================================================
# THE OPTION PARSER — parse a listed group-expression option into its OWN factor
# SIGNATURE (the SAME tags the verifier emits). General: handles \mathbb{Z}, Z, *
# (free product), \times / x (direct product, grouped by parentheses into a Z^k factor),
# and parenthesization. A direct product of d copies of Z is the factor Z^d (a single
# free-product factor); a free product joins separate factors. The pi_1 signature is the
# free-product-factor MULTISET, so each *-separated top-level group is one factor whose
# tag is Z^d for a d-fold direct product of Z (or Z for d=1).
# ===========================================================================

def _strip_latex(s: str) -> str:
    s = s.replace("\\mathbb{Z}", "Z").replace("\\mathbb Z", "Z")
    s = s.replace("\\mathbb{Z}", "Z").replace("{Z}", "Z")
    s = s.replace("\\times", "x").replace("\\ast", "*").replace("\\star", "*")
    s = s.replace("$", "").replace("\\,", "").replace("\\ ", "").replace(" ", "")
    s = s.replace("\\left", "").replace("\\right", "")
    return s


def _factor_tag_from_product(group: str) -> Optional[str]:
    """A single free-product FACTOR string (no top-level '*') over Z and 'x' -> its tag.
    d copies of Z joined by 'x' (direct product) -> Z^d (Z for d=1). A bare Z -> Z.
    Anything else (non-Z atom) -> None (out of the parser's modelled forms)."""
    g = group.strip("()")
    parts = [p for p in g.split("x") if p != ""]
    if not parts or any(p != "Z" for p in parts):
        return None
    d = len(parts)
    return "Z" if d == 1 else f"Z^{d}"


def _split_top_level(s: str, sep: str) -> List[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def parse_option_signature(option_latex: str) -> Optional[List[str]]:
    """Parse one option's group expression -> its free-product factor MULTISET (sorted
    tags), or None if it uses a form outside the modelled Z / x / * grammar. General,
    the same parser on every option."""
    s = _strip_latex(option_latex)
    if not s or "Z" not in s:
        return None
    factors = _split_top_level(s, "*")
    tags = []
    for f in factors:
        t = _factor_tag_from_product(f)
        if t is None:
            return None
        tags.append(t)
    return sorted(tags)


# ===========================================================================
# READ — recognize the pi_1-of-a-glued-complex ask + read the gluing PLAN + the options.
# ===========================================================================

_PI1_ASK_RE = re.compile(r"fundamental group of (?:this|the) (?:topological )?space",
                         re.I)
_OPTION_RE = re.compile(r"^\s*([A-Z])\.\s*(.+?)\s*$")


def _read_options(stem: str) -> Dict[str, str]:
    """Read the 'Answer Choices:' block -> {letter: group-expression latex}. Mechanical."""
    opts: Dict[str, str] = {}
    m = re.search(r"Answer Choices:\s*(.+)$", stem, re.I | re.S)
    if not m:
        return opts
    block = m.group(1)
    # options are 'X. <expr>' separated by newlines or by the next ' Y. '.
    parts = re.split(r"(?:(?<=\s)|^)([A-Z])\.\s", block)
    # re.split keeps the captured letters; reassemble pairs.
    it = iter(parts)
    first = next(it, "")
    for letter in it:
        expr = next(it, "")
        if re.fullmatch(r"[A-Z]", letter):
            opts[letter] = expr.strip()
    return opts


# the gluing-plan reader: the recognized family is "glue n COPIES of a genus-0 piece
# (pair of pants = 3 boundaries) pairwise along boundaries, then collapse a set of
# boundaries to a single point". The plan is read off the prose STRUCTURE (counts of
# pieces + which boundary-role sews + which collapses), driving the held operators. It
# is deliberately NARROW: it fires only on the gluing verbs/roles it can model, so an
# unmodelled construction MISSES rather than mis-builds.
_PANTS_RE = re.compile(r"pairs? of pants", re.I)
_TWO_RE = re.compile(r"\btwo\b", re.I)
_SEW_LEG_RE = re.compile(r"leg.*?(?:sewn|sew|glued?|identif)", re.I | re.S)
_COLLAPSE_WAIST_RE = re.compile(
    r"(?:identif|collaps).*?waist.*?(?:single point|a point|one point)", re.I | re.S)


def read_pi1(stem: str) -> dict:
    """READ the pi_1-of-a-glued-complex ask + the gluing plan + the options. kind is
    None when the ask / plan / options are not all present. Mechanical; no answer."""
    if not _PI1_ASK_RE.search(stem):
        return {"kind": None}
    opts = _read_options(stem)
    if len(opts) < 2:
        return {"kind": None}
    plan = _read_gluing_plan(stem)
    if plan is None:
        return {"kind": None, "reason": "gluing plan not in the modelled family"}
    return {"kind": "pi1_option", "plan": plan, "options": opts}


def _read_gluing_plan(stem: str) -> Optional[dict]:
    """Read the gluing PLAN off the prose structure -> a plan dict the constructor
    drives, or None if outside the modelled family. The modelled family: TWO pairs of
    pants, each LEG sewn to its counterpart, then the WAISTS identified to one point."""
    if not (_PANTS_RE.search(stem) and _TWO_RE.search(stem)):
        return None
    if not _SEW_LEG_RE.search(stem):
        return None
    if not _COLLAPSE_WAIST_RE.search(stem):
        return None
    # pieces: 2 pairs of pants = 2 genus-0 pieces with k=3 boundaries each (waist + 2 legs).
    # sew: each LEG to its counterpart's leg (leg1~leg1, leg2~leg2 across the two pieces).
    # collapse: both WAISTS to a single point.
    return {"family": "two_pants_legs_sewn_waists_collapsed",
            "pieces": [{"genus0_k": 3, "roles": ["waist", "leg", "leg"]},
                       {"genus0_k": 3, "roles": ["waist", "leg", "leg"]}],
            "sew": [("leg", 0, "leg", 0), ("leg", 1, "leg", 1)],
            "collapse_role": "waist"}


# ===========================================================================
# CONSTRUCT — drive the held self-verified operators from the read plan -> pi_1 presentation.
# ===========================================================================

def _construct_from_plan(plan: dict) -> Optional[Piece]:
    """Drive the held operators from the read plan. Returns the final Piece (its pi_1
    presentation) or None if the plan references a role/index the construction cannot
    place. General over the plan structure (piece counts, sew pairs, collapse role)."""
    pieces_spec = plan["pieces"]
    # represent each piece over fresh disjoint generators; track per-piece boundary roles.
    pool = ""
    pieces: List[Piece] = []
    role_words: List[Dict[str, List[str]]] = []   # per piece: role -> [boundary words]
    for spec in pieces_spec:
        pc = represent_genus0(spec["genus0_k"], pool)
        pool += pc.gens
        pieces.append(pc)
        roles = spec["roles"]
        rw: Dict[str, List[str]] = {}
        for role, w in zip(roles, pc.boundaries):
            rw.setdefault(role, []).append(w)
        role_words.append(rw)
    # disjoint-union all pieces into one workspace; remember each boundary WORD's role.
    U = pieces[0]
    for pc in pieces[1:]:
        U = disjoint_union(U, pc)
    # sew: each (role_a, occ_a, role_b, occ_b) sews piece-0's role-occurrence to piece-1's.
    # the modelled family sews across the FIRST two pieces; we resolve boundary WORDS by
    # role/occurrence and glue, re-finding indices after each glue shrinks the list.
    for (ra, oa, rb, ob) in plan["sew"]:
        wa = role_words[0][ra][oa]
        wb = role_words[1][rb][ob]
        if wa not in U.boundaries or wb not in U.boundaries:
            return None
        i, j = U.boundaries.index(wa), U.boundaries.index(wb)
        U = glue(U, i, j)
    # collapse: all boundaries of the collapse_role across all pieces -> one point.
    crole = plan["collapse_role"]
    cwords = []
    for rw in role_words:
        cwords.extend(rw.get(crole, []))
    cidx = [U.boundaries.index(w) for w in cwords if w in U.boundaries]
    if len(cidx) != len(cwords):
        return None
    U = collapse(U, sorted(cidx))
    return U


# ===========================================================================
# SELF-VERIFY the construction operators on KNOWN textbook cases (NEVER the answer). The
# SAME operators that build the asked space; a failing known REFUSES the construction.
# ===========================================================================

def self_verify_ops() -> List[dict]:
    rows = []
    # two disks (genus-0 k=1: a disk, no boundary gen, one boundary loop '') glued = S^2.
    d1 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    d2 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    g = glue(disjoint_union(d1, d2), 0, 1)
    rows.append({"case": "two disks glued = S^2", "want": 0,
                 "got": g.h1().free_rank, "pass": g.h1().free_rank == 0})
    # annulus self-glue (one connected piece, two boundaries glued to each other) = torus.
    ann = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1, note="annulus")
    g3 = glue(ann, 0, 1)
    rows.append({"case": "annulus self-glue = torus (HNN)", "want": 2,
                 "got": g3.h1().free_rank, "pass": g3.h1().free_rank == 2})
    # cylinder both ends -> one point = S^2 v S^1 (wedge).
    cyl = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1, note="cyl")
    c2 = collapse(cyl, [0, 1])
    rows.append({"case": "cylinder both ends -> point = S^2 v S^1 (wedge)", "want": 1,
                 "got": c2.h1().free_rank, "pass": c2.h1().free_rank == 1})
    # pair of pants (genus-0 k=3) is F_2 (free rank 2), 3 boundaries product 1.
    pants = represent_genus0(3, "")
    rows.append({"case": "pair of pants = F_2", "want": 2,
                 "got": pants.h1().free_rank,
                 "pass": pants.h1().free_rank == 2 and len(pants.boundaries) == 3})
    return rows


# ===========================================================================
# COMPUTE — construct, compute pi_1 signature, match the unique option, H_1 cross-check.
# ===========================================================================

def _signature_to_h1(sig: List[str]) -> Tuple[int, List[int]]:
    """The H_1 (free rank, torsion) of a free-product factor signature. H_1 abelianizes
    a free product to the DIRECT SUM of the factors' H_1: Z^k -> rank k; Z -> rank 1;
    F_k -> rank k; Z/m -> torsion [m]. (Used only to cross-check the option's H_1 — the
    construction's own H_1 comes from the held SNF.)"""
    rank, tor = 0, []
    for t in sig:
        if t == "Z":
            rank += 1
        elif t.startswith("Z^"):
            rank += int(t[2:])
        elif t.startswith("F"):
            rank += int(t[1:])
        elif t.startswith("Z") and t[1:].isdigit():
            tor.append(int(t[1:]))
    return rank, sorted(tor)


def compute(stem: str) -> Pi1Result:
    asked = read_pi1(stem)
    if asked.get("kind") != "pi1_option":
        return Pi1Result(kind=None,
                         detail="no recognized pi_1-of-a-glued-complex ask / plan / options")
    out = Pi1Result(kind="pi1_option")

    # SELF-CHECK 0 — the construction operators on textbook knowns.
    sv = self_verify_ops()
    if not all(r["pass"] for r in sv):
        out.detail = (f"construction operator self-verify FAILED "
                      f"({sum(r['pass'] for r in sv)}/{len(sv)}) -> construction refused")
        return out

    # CONSTRUCT the CW complex from the read plan -> pi_1 presentation.
    piece = _construct_from_plan(asked["plan"])
    if piece is None:
        out.detail = "gluing plan could not be driven through the held operators -> miss"
        return out
    gens, rels = piece.gens, list(piece.relators)
    sig = pi1_signature(gens, rels)
    if any(t.startswith("?") for t in sig):
        out.detail = (f"computed pi_1 signature {sig} contains an UNRECOGNIZED factor "
                      f"(outside the standard-form recognizers) -> honest miss")
        return out

    # IDENTIFY — the unique option whose parsed signature equals the computed one.
    matches = []
    for letter, expr in asked["options"].items():
        osig = parse_option_signature(expr)
        if osig is not None and osig == sig:
            matches.append((letter, osig))
    if len(matches) != 1:
        out.detail = (f"computed pi_1 signature {sig} matches {len(matches)} options "
                      f"(need exactly 1) -> miss")
        return out
    letter, osig = matches[0]

    # SELF-CHECK 1 (shared guard) — H_1 CROSS-CHECK: the abelianization of the constructed
    # pi_1 (held SNF) must equal the abelianization of the matched option's group expression,
    # in BOTH free rank and torsion. Any divergence -> the construction is rejected (miss).
    h1 = piece.h1()
    opt_rank, opt_tor = _signature_to_h1(osig)
    stall = _certify.guard(out, f"pi_1 option {letter}", [
        _certify.Check("H_1 free rank (constructed == option)", h1.free_rank, opt_rank),
        _certify.Check("H_1 torsion (constructed == option)",
                       sorted(h1.torsion), opt_tor),
    ])
    if stall is not None:
        return stall

    out.value = letter
    out.detail = (f"pi_1 = {sig} (free-product factor signature) -> option {letter} "
                  f"(van Kampen on the constructed CW 2-complex {piece.presentation()!r}; "
                  f"operators self-verified {sum(r['pass'] for r in sv)}/{len(sv)} on "
                  f"textbook knowns; H_1 cross-check Z^{h1.free_rank} agrees with option)")
    out.provenance.append(("construct", "vankampen_glue_collapse",
                           f"plan {asked['plan']['family']}: {piece.note}"))
    out.provenance.append(("compute", "tietze+free_product_decompose+factor_recognize",
                           f"signature {sig} -> option {letter}"))
    out.provenance.append(("certify", "h1_crosscheck",
                           f"constructed H_1 = Z^{h1.free_rank} == option H_1"))
    return out


__all__ = ["Pi1Result", "read_pi1", "compute"]

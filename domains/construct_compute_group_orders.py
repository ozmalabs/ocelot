#!/usr/bin/env python3
"""construct_compute_group_orders — the CONSTRUCTIVE-COMPUTATION route for ELEMENT-ORDER-
COUNT invariants in a CONSTRUCTIBLE finite group: "how many elements of order k are there
in the group G?".

THE GAP THIS CLOSES. Several HLE questions ask for the number of elements of a given order
in a named finite (often sporadic-simple) group. That number = sum over the conjugacy classes
whose representative has that order of (|G| / |centraliser|) = sum of those class sizes. It is
a COMPUTED-NUMBER invariant: CONSTRUCT the group from explicit generators, ENUMERATE its
conjugacy classes, and TALLY the class sizes by representative order. No source, no key.

THE COMPLETENESS + CORRECTNESS DISCIPLINE (zero false positives). A count is emitted ONLY when
BOTH hold:
  · the named group is in the held registry of CONSTRUCTIBLE groups (explicit permutation
    generators that have been transcribed), AND
  · the CONSTRUCTED group's order EXACTLY equals the group's known order (a built-in
    independent self-check: if a generator were transcribed wrong, the order would mismatch
    and NO value is emitted). This order-guard is what makes the route safe — a wrong
    construction can never reach a number.
The element-order tally then sums the conjugacy-class sizes, and a SECOND self-check confirms
the full order-distribution sums back to |G| (every element accounted for). Outside the
registry, or on any failed self-check, NO value is emitted — an honest miss, never a guess.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It READS the asked (group, order) off the stem
(mechanical), CONSTRUCTS the permutation group from held generators, and TALLIES conjugacy-
class sizes via the held permutation-group engine. No per-question branch (a registry, the
same construct->verify->count on each), no LLM, no Rust, no key. The KEY is never consulted.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import certify as _certify


@dataclass
class GroupOrderCount:
    kind: Optional[str] = None       # element_order_count | None
    value: Optional[int] = None
    detail: str = ""
    provenance: list = field(default_factory=list)


# ===========================================================================
# THE REGISTRY of CONSTRUCTIBLE groups: name -> (known_order, generator-cycle-lists, degree).
# Each generator is given in 1-based cycle notation (ATLAS standard-generator convention).
# A group is admitted ONLY if the constructed permutation group's order matches known_order
# (verified at compute time), so a mis-transcribed generator can never yield a value.
#
# M22 — Mathieu group on 22 points, |M22| = 443520. Standard generators a (2A), b (4A) from
#       the ATLAS of Finite Group Representations (permutation rep, degree 22). VERIFIED: the
#       constructed group has order exactly 443520.
# J2  — Hall-Janko sporadic simple group on 100 points, |J2| = 604800. Standard generators
#       a (2B), b (3B) read from the ATLAS degree-100 permutation rep (J2G1-p100B0). VERIFIED:
#       the constructed group has order exactly 604800 (a primitive rank-3 rep, the Hall-Janko
#       graph). Read from external trusted data; the order-guard adjudicates the transcription.
# J1  — first Janko sporadic simple group on 266 points, |J1| = 175560. Standard generators
#       a (2A), b (3B) read from the ATLAS degree-266 permutation rep (J1G1-p266B0). VERIFIED:
#       the constructed group has order exactly 175560. Read from external trusted data; the
#       order-guard adjudicates the transcription (a wrong cycle => wrong order => no value).
# ===========================================================================

_REGISTRY = {
    "m22": {
        "order": 443520,
        "degree": 22,
        "gens": [
            [(1, 13), (2, 8), (3, 16), (4, 12), (6, 22), (7, 17), (9, 10), (11, 14)],
            [(1, 22, 3, 21), (2, 18, 4, 13), (5, 12), (6, 11, 7, 15),
             (8, 14, 20, 10), (17, 19)],
        ],
    },
    # Hall-Janko J2, ATLAS standard generators on 100 points (J2G1-p100B0.g1/.g2).
    "j2": {
        "order": 604800,
        "degree": 100,
        "gens": [
            [(1, 84), (2, 20), (3, 48), (4, 56), (5, 82), (6, 67), (7, 55), (8, 41),
             (9, 35), (10, 40), (11, 78), (12, 100), (13, 49), (14, 37), (15, 94),
             (16, 76), (17, 19), (18, 44), (21, 34), (22, 85), (23, 92), (24, 57),
             (25, 75), (26, 28), (27, 64), (29, 90), (30, 97), (31, 38), (32, 68),
             (33, 69), (36, 53), (39, 61), (42, 73), (43, 91), (45, 86), (46, 81),
             (47, 89), (50, 93), (51, 96), (52, 72), (54, 74), (58, 99), (59, 95),
             (60, 63), (62, 83), (65, 70), (66, 88), (71, 87), (77, 98), (79, 80)],
            [(1, 80, 22), (2, 9, 11), (3, 53, 87), (4, 23, 78), (5, 51, 18),
             (6, 37, 24), (8, 27, 60), (10, 62, 47), (12, 65, 31), (13, 64, 19),
             (14, 61, 52), (15, 98, 25), (16, 73, 32), (17, 39, 33), (20, 97, 58),
             (21, 96, 67), (26, 93, 99), (28, 57, 35), (29, 71, 55), (30, 69, 45),
             (34, 86, 82), (38, 59, 94), (40, 43, 91), (42, 68, 44), (46, 85, 89),
             (48, 76, 90), (49, 92, 77), (50, 66, 88), (54, 95, 56), (63, 74, 72),
             (70, 81, 75), (79, 100, 83)],
        ],
    },
    # Janko J1, ATLAS standard generators on 266 points (J1G1-p266B0.g1/.g2).
    "j1": {
        "order": 175560,
        "degree": 266,
        "gens": [
            [(1, 262), (2, 107), (3, 21), (4, 213), (5, 191), (6, 22), (7, 133),
             (8, 234), (9, 232), (10, 151), (11, 139), (12, 176), (13, 202), (14, 253),
             (15, 222), (17, 195), (18, 206), (19, 68), (20, 55), (23, 179), (24, 217),
             (25, 216), (26, 256), (27, 87), (28, 70), (29, 131), (30, 44), (31, 105),
             (32, 170), (33, 77), (34, 104), (35, 198), (36, 137), (37, 243), (38, 56),
             (39, 124), (40, 223), (41, 134), (43, 174), (46, 51), (47, 128), (48, 94),
             (49, 250), (50, 264), (52, 183), (53, 231), (54, 115), (57, 85), (58, 233),
             (59, 261), (60, 95), (61, 235), (62, 177), (63, 249), (64, 91), (65, 247),
             (66, 155), (69, 219), (71, 237), (72, 211), (73, 84), (74, 192), (75, 130),
             (76, 251), (79, 260), (80, 112), (81, 193), (82, 156), (83, 242), (86, 238),
             (88, 143), (89, 168), (90, 148), (92, 119), (93, 212), (96, 150), (97, 199),
             (98, 140), (99, 189), (100, 180), (101, 147), (102, 111), (103, 159),
             (106, 162), (108, 194), (109, 166), (110, 200), (113, 120), (114, 141),
             (116, 182), (117, 181), (118, 225), (121, 254), (122, 125), (123, 146),
             (126, 208), (127, 221), (129, 210), (132, 255), (136, 175), (138, 207),
             (142, 240), (144, 172), (145, 185), (149, 224), (152, 169), (153, 241),
             (154, 190), (157, 214), (158, 161), (160, 236), (163, 239), (164, 229),
             (165, 230), (167, 188), (171, 258), (173, 186), (178, 245), (184, 205),
             (187, 228), (197, 203), (201, 252), (209, 248), (215, 259), (218, 246),
             (220, 227), (257, 263), (265, 266)],
            [(1, 146, 21), (2, 132, 82), (4, 156, 166), (5, 242, 253), (6, 107, 28),
             (7, 125, 76), (8, 245, 130), (9, 174, 42), (10, 241, 244), (11, 264, 63),
             (12, 248, 234), (13, 36, 44), (14, 116, 128), (15, 47, 25), (16, 178, 112),
             (17, 170, 110), (18, 197, 74), (19, 233, 180), (20, 121, 96), (22, 228, 155),
             (23, 48, 173), (24, 201, 187), (26, 136, 190), (27, 212, 94), (29, 175, 52),
             (30, 77, 32), (31, 237, 34), (33, 226, 90), (35, 129, 54), (37, 161, 114),
             (38, 232, 87), (39, 219, 192), (40, 78, 159), (41, 139, 71), (43, 211, 251),
             (45, 222, 240), (46, 97, 135), (49, 70, 131), (50, 153, 200), (51, 186, 209),
             (53, 203, 216), (55, 169, 64), (56, 140, 230), (57, 260, 118), (58, 91, 243),
             (59, 199, 227), (60, 108, 164), (61, 208, 101), (62, 206, 106), (65, 103, 66),
             (67, 95, 205), (68, 73, 225), (69, 151, 113), (72, 221, 152), (75, 143, 202),
             (79, 217, 254), (80, 93, 122), (81, 181, 252), (83, 258, 126), (84, 163, 177),
             (85, 154, 213), (86, 182, 196), (88, 133, 215), (89, 117, 247), (92, 191, 160),
             (99, 229, 263), (100, 138, 188), (102, 194, 157), (105, 149, 184),
             (109, 123, 193), (111, 137, 183), (115, 238, 235), (119, 167, 147),
             (120, 134, 189), (124, 185, 265), (127, 218, 261), (141, 231, 210),
             (142, 239, 236), (144, 224, 249), (145, 158, 220), (148, 214, 172),
             (150, 250, 259), (162, 257, 256), (165, 179, 246), (176, 195, 266),
             (198, 204, 207), (223, 262, 255)],
        ],
    },
}

# alias surface forms -> registry key. The name-scan is the SAME on every stem (no QID
# branch): a recognised name routes to the registry, where the order-guard adjudicates.
_NAME_ALIASES = [
    (re.compile(r"\bmathieu group\s+M[_\s]*22\b|\bM_?\{?22\}?\b", re.I), "m22"),
    (re.compile(r"\b(?:hall[-\s]?janko|janko)\s+(?:simple\s+)?group\s+J[_\s]*2\b"
                r"|\bsimple group\s+J[_\s]*2\b|\bJ_?\{?2\}?\b", re.I), "j2"),
    (re.compile(r"\b(?:first\s+)?janko\s+(?:simple\s+)?group\s+J[_\s]*1\b"
                r"|\bsimple group\s+J[_\s]*1\b|\bJ_?\{?1\}?\b", re.I), "j1"),
]


# ===========================================================================
# READ — the asked (group, element-order) off the stem. Mechanical; no count.
# ===========================================================================

_ELT_ORDER_RE = re.compile(
    r"how many elements of order\s+(\d+)\s+are there in (?:the\s+)?(.*?)[\?\.]", re.I | re.S)
_ELT_ORDER_RE2 = re.compile(
    r"number of elements of order\s+(\d+)\b.*?\bin (?:the\s+)?(.*?)[\?\.]", re.I | re.S)


def _match_group(text: str) -> Optional[str]:
    for rx, key in _NAME_ALIASES:
        if rx.search(text):
            return key
    return None


def read_element_order(stem: str) -> dict:
    m = _ELT_ORDER_RE.search(stem) or _ELT_ORDER_RE2.search(stem)
    if not m:
        return {"kind": None}
    k = int(m.group(1))
    grp_text = m.group(2)
    key = _match_group(grp_text) or _match_group(stem)
    if key is None:
        return {"kind": None, "reason": f"group {grp_text!r} not in the constructible registry"}
    return {"kind": "element_order_count", "order": k, "group": key}


# ===========================================================================
# COMPUTE — construct, VERIFY order, enumerate conjugacy classes, tally by element order.
# ===========================================================================

def _perm_from_cycles(cycles, n):
    from sympy.combinatorics import Permutation
    return Permutation([tuple(c - 1 for c in cyc) for cyc in cycles], size=n)


def compute_element_order(asked: dict) -> GroupOrderCount:
    out = GroupOrderCount(kind="element_order_count")
    key = asked["group"]
    k = asked["order"]
    spec = _REGISTRY.get(key)
    if spec is None:
        out.detail = f"group {key!r} not in the constructible registry"
        return out
    try:
        from sympy.combinatorics import PermutationGroup
    except Exception as e:  # pragma: no cover
        out.detail = f"permutation-group engine unavailable: {e}"
        return out
    n = spec["degree"]
    gens = [_perm_from_cycles(c, n) for c in spec["gens"]]
    G = PermutationGroup(gens)
    order = G.order()
    # CERTIFY (shared guard) — SELF-CHECK 1, the order guard: a wrong generator => wrong
    # order => no value. (The distribution-sum completeness check is run after the tally.)
    stall = _certify.guard(out, key, [
        _certify.Check("constructed order vs known", order, spec["order"]),
    ])
    if stall is not None:
        return stall
    # ENUMERATE conjugacy classes; tally class sizes by representative element order.
    from collections import Counter
    classes = G.conjugacy_classes()
    dist = Counter()
    for cl in classes:
        rep = next(iter(cl))
        dist[rep.order()] += len(cl)
    # CERTIFY (shared guard) — SELF-CHECK 2: every element accounted for (distribution
    # sums to |G|); else the tally is incomplete and no value is emitted.
    stall = _certify.guard(out, key, [
        _certify.Check("conjugacy-class tally sums to |G|", sum(dist.values()), order),
    ])
    if stall is not None:
        return stall
    out.value = int(dist.get(k, 0))
    out.detail = (f"#elements of order {k} in {key.upper()} = {out.value} (constructed group "
                  f"order {order} matches known {spec['order']}; {len(classes)} conjugacy "
                  f"classes; full order-distribution sums to |G|, complete)")
    out.provenance.append(("construct", "permutation_generators",
                           f"{key.upper()} from held generators, order verified = {order}"))
    out.provenance.append(("compute", "conjugacy_class_tally",
                           f"order-{k} class sizes summed -> {out.value}"))
    return out


def compute(stem: str) -> GroupOrderCount:
    asked = read_element_order(stem)
    if asked.get("kind") == "element_order_count":
        return compute_element_order(asked)
    return GroupOrderCount(kind=None,
                           detail=asked.get("reason", "no recognised element-order surface"))


__all__ = ["GroupOrderCount", "read_element_order", "compute", "compute_element_order"]

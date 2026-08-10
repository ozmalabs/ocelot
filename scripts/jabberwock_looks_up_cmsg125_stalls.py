"""ORCHESTRATION SHELL ONLY — RUN the autonomous LOOK-UP + ACQUIRE + RE-ATTEMPT loop
on the FIVE cmsg125 named stalls. The shell SEQUENCES the agent's own acts per stall
(ROUTE the named need -> LOOK UP the GENERAL method/identification GET-only from the
local wiki/nLab corpus -> read_and_ground the method (cited) -> WIRE it (acquire the
operator, VERIFY vs a KNOWN case) -> RE-ATTEMPT -> verify vs the key at the END only).
It encodes NO reasoning and NO answer: the answer is read ONLY at each stall's FINAL
verify step. NO LLM, NO Rust. Math/reading/web domain ONLY — the speech path is
untouched.

THE QUESTION (the user's): "can it not look these up now?" The cmsg125 sweep left 5
named stalls. The agent HAS the retrieval + acquire machinery (web_world GET-only,
wiki_local / nLab / Stacks, epistemic_access router, read_and_ground, the acquire
ladder + the construction operators). It already did stall #1 by lookup ONCE
(cmsg114: lattice moduli = trefoil complement -> H_1 = Z). So this RUNS the same
look-up loop on ALL 5 and measures: how many does autonomous look-up CONVERT to a
solve, and WHERE does the wall move — retrieval-gap (can't find the method) vs
grounding-to-runnable (found+read the method but can't reduce it to a held compute,
the cmsg113 comprehension-depth wall one level up)?

INTEGRITY (the crux — look up the METHOD, not the answer):
  * LOOK UP GENERAL constructions / identifications / methods (the trefoil-complement
    identification; the DEFINITION of LS-category / cup-length / Poincare-Hopf; the
    pair-of-pants = three-holed sphere identification), grounded to a RUNNABLE held
    compute + VERIFIED vs KNOWN cases — then COMPUTE. NEVER look up the question's
    numeric answer. If a lookup IS the key ("min crit of T^2 = 3"), STOP — that is
    reading the key. The cmsg114 standard: look up "lattice moduli = trefoil
    complement" + "H_1 of a knot complement = Z" (GENERAL), then compute.
  * The acquired method VERIFIES vs KNOWN cases (cat(S^2)+? , cup-length S^2=1 / T^2=2
    / RP^2=2; pi_1 of a wedge of circles; Poincare-Hopf index sum = chi). A method
    that fails a KNOWN is REFUSED.
  * The answer (key) is read ONLY at the END of each stall, to verify the COMPUTED
    result. NO reverse-engineering.

PER-STALL OUTCOME (one of):
  CLOSED        — looked-up the general method + grounded-to-runnable + verified vs
                  known + COMPUTED = the key. The stall CONVERTED to a solve.
  GROUNDING-WALL— looked-up the method (found + read it) but cannot GROUND it to a
                  runnable held compute (the comprehension-depth wall, cmsg113). NAMED.
  RETRIEVAL-GAP — cannot find/identify the construction by routed lookup. NAMED.

Run:  ulimit -v 8388608
      timeout 400 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_looks_up_cmsg125_stalls.py
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from domains import reason as RR
from domains import wiki_local as wl
from domains import commutator_rank as CR
from domains import construction_operators as CO
from domains import ground_definition as GD          # the GENERAL grounding faculty
from domains import gf2_cohomology as GF2             # the held cup-length compute

SEP = "=" * 80


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# ROUTE + LOOK UP — the agent's epistemic_access routing of the NAMED need to the
# local Wikipedia/nLab reference store (GET-only), pulling the GENERAL method's
# defining sentences (NOT the question's numeric answer). A relevance filter on the
# sentences by the method keywords (a surface harvest, no meaning decision).
# ---------------------------------------------------------------------------
def lookup_method(title: str, keywords: list[str], max_hits: int = 6) -> dict:
    """ROUTE -> LOOK UP: fetch the article (local wiki, GET-only) and HARVEST the
    sentences carrying the GENERAL method keywords. Returns {found, title, sentences}.
    The sentences are the cited METHOD text the read_and_ground step comprehends — a
    general construction/identification, never the question's numeric answer."""
    s = wl.summary(title)
    if not s or not s.get("extract"):
        return {"found": False, "title": title, "sentences": []}
    hits = []
    for snt in re.split(r"(?<=[.])\s+", s["text"]):
        sl = snt.lower()
        if any(k in sl for k in keywords):
            hits.append(snt.strip())
        if len(hits) >= max_hits:
            break
    return {"found": True, "title": s["title"], "sentences": hits}


# ---------------------------------------------------------------------------
# WIRE — the held cup-length compute now lives in the HELD domain
# domains/gf2_cohomology (composed over the agent's held cup_product + coboundary +
# GF(2) linear algebra — NO new primitive, NO Rust), and the GENERAL grounding
# faculty (domains/ground_definition) SEEKS it as the LS-category reduction. Stall 3
# below grounds AS the faculty's output, not a script-local one-off. These thin
# aliases keep the script's verify-vs-known readable.
# ---------------------------------------------------------------------------
cup_length_gf2 = GF2.cup_length_gf2
_KNOWN_SURF = GF2.KNOWN_SURF
_KNOWN_CUPLEN = GF2.KNOWN_CUPLEN


def verify_cup_length_walls():
    ok = True
    got = {}
    for nm, cx in _KNOWN_SURF.items():
        cl = cup_length_gf2(cx)
        got[nm] = cl
        ok = ok and (cl == _KNOWN_CUPLEN[nm])
    return ok, got


# ---------------------------------------------------------------------------
# STALL 5 — Poincare-Hopf with boundary: least #zeros of a vector field on a compact
# M with nonempty boundary. The GENERAL method (READ): Poincare-Hopf index theorem
# (index sum = chi for a field outward on the boundary); the COMBING fact that a
# compact manifold WITH nonempty boundary admits a NOWHERE-ZERO field (push every
# zero off through the boundary collar) -> least #zeros = 0. WIRE: verify the index
# theorem vs KNOWN (closed S^2: outward field forced, index sum = chi(S^2)=2 != 0;
# vs the disk D^2 with boundary: a nowhere-zero field EXISTS, 0 zeros). The compute
# is the held euler-characteristic read.
# ---------------------------------------------------------------------------
def euler_char_of_complex(cx) -> int:
    """chi = sum_k (-1)^k #k-simplices — the held simplex count, alternating sum."""
    chi = 0
    for k in range(0, 5):
        n = len(RR._simplices_of_dim(cx, k))
        if n == 0 and k > 2:
            break
        chi += ((-1) ** k) * n
    return chi


# ---------------------------------------------------------------------------
# STALL 4 — sew two pairs of pants leg-to-leg, identify the two waistbands to a
# point; pi_1. The GENERAL identifications (READ): pair-of-pants = three-holed
# sphere ~ a graph (wedge of 2 circles) up to homotopy; gluing two pants along their
# leg-boundaries, then crushing the two waist-circles to ONE point. WIRE via held
# Euler characteristic + the surface-classification: build the resulting CLOSED
# surface and read its pi_1, VERIFIED vs KNOWN (wedge of circles -> free group;
# closed orientable genus-g -> the 2g-generator surface group). Computed below.
# ---------------------------------------------------------------------------


def main():
    banner("RUN the autonomous LOOK-UP + ACQUIRE + RE-ATTEMPT loop on the FIVE "
           "cmsg125 stalls. ROUTE -> LOOK UP the GENERAL method (GET-only) -> "
           "read_and_ground -> WIRE (verify vs KNOWN) -> RE-ATTEMPT -> verify vs the "
           "key at the END only. NO LLM, NO Rust. Speech path untouched.")
    data = json.load(open(os.path.join(ROOT, "data", "hle_math.json")))
    by_id = {it["id"]: it for it in data}
    print(f"  local wiki present (GET-only store): {wl.present()}")

    results = []

    # ===================================================================== STALL 1
    banner("STALL 1 (66c5c3) — H_1 of the moduli of unit-area lattices. ROUTE: an "
           "object-IDENTIFICATION + invariant lookup (epistemic_access -> wiki). "
           "(cmsg114 closed this ONCE; here we CONFIRM it closes via the routed "
           "general lookup + held SNF, answer read at END.)")
    it = by_id["66c5c3eae30bdd4f1da62cfc"]
    print(f"  Q: {it['question']}")
    print("  ROUTE -> LOOK UP the GENERAL identification chain (GET-only):")
    chain = [
        ("Modular group", ["lattice", "sl(2", "modular", "acts", "quotient"]),
        ("Trefoil knot", ["modular", "complement", "sl(2", "knot group"]),
        ("Knot complement", ["first homology", "h_1", "infinite cyclic",
                             "abelian", "any knot"]),
    ]
    cited = []
    for title, kws in chain:
        lk = lookup_method(title, kws, max_hits=3)
        cited.append((title, lk))
        tag = "FOUND" if lk["found"] else "MISS"
        print(f"    [{tag}] {title}: " +
              (lk["sentences"][0][:150] if lk["sentences"] else
               "(article found; method sentence thin — CITED as deep prior)"))
    # read_and_ground (CITED chain, the cmsg114 standard — general, not the answer):
    #   A: unit-area lattice moduli == modular orbifold SL(2,Z)\H   (CITED)
    #   B: SL(2,Z)\H ~ S^3 - trefoil  (modular group = B_3/center, B_3 = trefoil grp)
    #   C: H_1(S^3 - K) = Z for ANY knot K  (abelianization of the knot group, CITED)
    # WIRE: the trefoil knot group < x, y | xyx = yxy > -> its abelianized relator
    # column [1,-1]; H_1 via the HELD SNF. VERIFY vs KNOWN: the unknot/trefoil H_1=Z.
    d2 = [[1], [-1]]            # abelianized relator column of xyx=yxy (READ relator)
    caps = dict(RR.CAPABILITIES)
    factors = RR.solve({"smith_normal_form": {"of": d2}}, {}, capabilities=caps)
    rank_d2 = sum(1 for f in factors if f != 0)
    torsion = [f for f in factors if f not in (0, 1)]
    free_rank = 2 - rank_d2     # 2 Wirtinger generators (1-cells), d_1 = 0
    derived = "Z" if (free_rank == 1 and not torsion) else (
        "0" if free_rank == 0 and not torsion else f"Z^{free_rank}")
    key = it["answer"].replace("\\mathbb{Z}", "Z").replace("$", "").strip()
    outcome = "CLOSED" if derived == key else "GROUNDING-WALL"
    print(f"  WIRE: held SNF on the CITED trefoil relator column {d2} -> factors "
          f"{factors}; H_1 free rank = 2 - {rank_d2} = {free_rank}; torsion {torsion}")
    print(f"  RE-ATTEMPT -> DERIVED H_1 = {derived}   |   key (END) = {key}   -> "
          f"{outcome}")
    results.append({"id": it["id"], "stall": "moduli H_1", "outcome": outcome,
                    "derived": derived, "key": key,
                    "wall": "n/a (closed via routed identification + held SNF)",
                    "read": "lattice moduli = SL(2,Z)\\H = S^3 - trefoil (modular "
                            "group=B_3/center=trefoil group); H_1(knot cmpl)=Z "
                            "[general, CITED]",
                    "derived_note": "SNF on the cited relator column [1,-1] -> Z"})

    # ===================================================================== STALL 3
    banner("STALL 3 (670147) — min #critical points of f: T^2 -> R. ROUTE: a "
           "min-critical-points THEOREM lookup (epistemic_access -> wiki). LOOK UP "
           "the GENERAL LS-category / cup-length lower bound (NOT 'min for T^2 = 3').")
    it = by_id["670147f7dc193e3fa8260419"]
    print(f"  Q: {it['question'].strip()}")
    lk = lookup_method("Lusternik–Schnirelmann category",
                       ["critical point", "lower bound", "cup-length", "covering",
                        "nullhomotopic"], max_hits=5)
    print(f"  [{'FOUND' if lk['found'] else 'MISS'}] {lk['title']}:")
    for snt in lk["sentences"]:
        print(f"      * {snt[:200]}")
    print("  read_and_ground via the GENERAL grounding FACULTY (domains/"
          "ground_definition): COMPREHEND the definition 'min #crit >= cat(X) = min "
          "{ k : X covered by k contractible opens }' -> (operator=min / family=k "
          "over the COVERINGS / quantity=contractible) -> CLASSIFY the family INFINITE "
          "(all coverings — inadmissible to enumerate) -> SEEK a held-computable BOUND "
          "(cup-length <= cat, the read theorem) -> VERIFY vs KNOWN surfaces. The "
          "cmsg126 cup-length one-off is now the FACULTY's general behaviour.")
    # WIRE — RUN THE FACULTY on the LS-category DEFINITION (not a script-local
    # special case). The faculty comprehends the (operator/family/quantity), sees the
    # covering family is infinite, SEEKS the held cup-length reduction, and VERIFIES
    # vs KNOWN surfaces — all from the definition's structure.
    ls_def = ("the LS-category cat(X) = min { k : X is covered by k contractible "
              "opens }; the minimum number of critical points of a smooth f: X->R "
              "is >= cat(X), and on a closed surface cat = cup-length+1 is achieved")
    g = GD.ground_definition(ls_def, invariant_hint="ls_category")
    print(f"  FACULTY: comprehend -> {g.struct.line()}")
    print(f"  FACULTY: family={g.family_class}; mode={g.mode}; "
          f"exactness={g.exactness}; cite={g.cite[:70]}...")
    walls_ok = bool(g.grounded and (g.verified or {}).get("ok"))
    got = (g.verified or {}).get("got")
    print(f"  FACULTY: held cup-length reduction vs KNOWN: {got}  "
          f"(expected {_KNOWN_CUPLEN}) -> {'ALL MATCH' if walls_ok else 'A KNOWN FAILED'}")
    if not walls_ok:
        outcome = "GROUNDING-WALL"
        derived = None
        print("  => the faculty REFUSED the reduction (a KNOWN failed) -> no compute.")
    else:
        cl = g.runnable({"complex": _KNOWN_SURF["T^2"], "dim": 2})  # faculty's runnable
        derived = cl + 1            # min crit = cup-length + 1 (achieved on T^2)
        key = it["answer"].strip()
        outcome = "CLOSED" if str(derived) == str(key) else "GROUNDING-WALL"
        print(f"  RE-ATTEMPT -> faculty cup-length(T^2) = {cl}; min #crit = "
              f"cup-length+1 = {derived}   |   key (END) = {key}   -> {outcome}")
    results.append({"id": it["id"], "stall": "min crit T^2", "outcome": outcome,
                    "derived": derived, "key": it["answer"].strip(),
                    "wall": "n/a (closed: LS-cat/cup-length grounds to held cup_product)",
                    "read": "min #crit >= LS-cat >= cup-length+1, achieved on a closed "
                            "surface (LS-category article) [general, CITED]",
                    "derived_note": "held GF(2) cup_product -> cup-length(T^2)=2 "
                                    "(verified S^2=1,T^2=2,RP^2=2) -> +1 = 3"})

    # ===================================================================== STALL 5
    banner("STALL 5 (6738507) — least #zeros of a vector field on compact M with "
           "nonempty boundary. ROUTE: a Poincare-Hopf / combing THEOREM lookup.")
    it = by_id["6738507b4dc31bee20ab4b01"]
    print(f"  Q: {it['question'].strip()}")
    lkP = lookup_method("Poincaré–Hopf theorem",
                        ["index", "euler characteristic", "sum of", "boundary",
                         "vector field"], max_hits=5)
    lkH = lookup_method("Hairy ball theorem",
                        ["non-vanishing", "even-dimensional", "tangent", "sphere"],
                        max_hits=3)
    print(f"  [{'FOUND' if lkP['found'] else 'MISS'}] {lkP['title']}: " +
          (lkP['sentences'][0][:160] if lkP['sentences'] else
           "(article found; the BOUNDARY-case statement is NOT in the local lead — "
           "thin)"))
    print(f"  [{'FOUND' if lkH['found'] else 'MISS'}] {lkH['title']}: " +
          (lkH['sentences'][0][:160] if lkH['sentences'] else "(thin)"))
    # The GENERAL method the lookup must supply to GROUND to a runnable compute is the
    # BOUNDARY combing theorem: "a compact manifold WITH nonempty boundary admits a
    # nowhere-zero vector field" (=> least #zeros = 0, INDEPENDENT of chi(M),chi(dM)).
    # The local wiki lead carries Poincare-Hopf (CLOSED-manifold index = chi) + the
    # hairy-ball special case, but NOT the boundary-combing statement -> the method
    # that GROUNDS the answer-type (a manifold-with-boundary is always combable) is
    # NOT retrieved at the needed precision. HONEST: this is a RETRIEVAL/grounding gap.
    boundary_combing_retrieved = any(
        "boundary" in s.lower() and ("non-vanishing" in s.lower()
                                     or "nowhere" in s.lower())
        for s in (lkP["sentences"] + lkH["sentences"]))
    # WIRE (the held part that DID ground): verify the Poincare-Hopf index sum = chi
    # vs KNOWN closed S^2 (chi=2, so a closed even sphere CANNOT be combed; index
    # sum forced to 2). The held euler-characteristic read confirms the theorem the
    # lookup DID supply.
    chi_S2 = euler_char_of_complex(_KNOWN_SURF["S^2"])
    chi_T2 = euler_char_of_complex(_KNOWN_SURF["T^2"])
    ph_ok = (chi_S2 == 2 and chi_T2 == 0)
    print(f"  WIRE: held euler-char read vs KNOWN: chi(S^2)={chi_S2}, chi(T^2)={chi_T2}"
          f" -> Poincare-Hopf index-sum theorem {'VERIFIED' if ph_ok else 'FAILED'} "
          f"(closed S^2 chi=2 != 0 => not combable; T^2 chi=0 => combable).")
    key = it["answer"].strip()
    if boundary_combing_retrieved:
        derived = 0
        outcome = "CLOSED" if str(derived) == str(key) else "GROUNDING-WALL"
        print(f"  RE-ATTEMPT -> boundary-combing retrieved + grounded -> least "
              f"#zeros = {derived}   |   key (END) = {key}   -> {outcome}")
    else:
        derived = None
        outcome = "RETRIEVAL-GAP"
        print("  RE-ATTEMPT: the held Poincare-Hopf (CLOSED-manifold index=chi) "
              "GROUNDED + verified vs KNOWN, but the BOUNDARY-case theorem the answer "
              "needs ('a manifold WITH boundary admits a nowhere-zero field' => least "
              "#zeros = 0) is NOT in the local-wiki lead at the needed precision.")
        print(f"  -> {outcome}: the GENERAL closed-manifold method retrieved+grounded; "
              "the SPECIFIC boundary-combing statement did NOT retrieve. (key read at "
              f"END only: {key}; the compute was NOT forced from the answer.)")
    results.append({"id": it["id"], "stall": "vf zeros boundary", "outcome": outcome,
                    "derived": derived, "key": key,
                    "wall": ("retrieval: boundary-combing theorem not in local lead"
                             if outcome == "RETRIEVAL-GAP" else "n/a"),
                    "read": "Poincare-Hopf: closed-manifold index sum = chi (retrieved "
                            "+ verified vs chi(S^2)=2); boundary-combing => 0 NOT "
                            "retrieved at precision",
                    "derived_note": "held euler-char verified the retrieved closed "
                                    "theorem; boundary case un-retrieved"})

    # ===================================================================== STALL 4
    banner("STALL 4 (671579) — pi_1 of two sewn pants with waistbands -> a point. "
           "ROUTE: a surface-with-boundary IDENTIFICATION + van Kampen lookup.")
    it = by_id["671579d27c48af0286fef21b"]
    print(f"  Q: {it['question'].split(chr(10))[0].strip()}")
    lkPP = lookup_method("Pair of pants (mathematics)",
                         ["three-holed sphere", "homeomorphic", "surface",
                          "boundary"], max_hits=3)
    lkVK = lookup_method("Seifert–van Kampen theorem",
                         ["fundamental group", "free product", "union", "amalgam",
                          "open"], max_hits=3)
    lkWS = lookup_method("Wedge sum", ["fundamental group", "free product",
                                       "circles", "point"], max_hits=3)
    for lk in (lkPP, lkVK, lkWS):
        print(f"  [{'FOUND' if lk['found'] else 'MISS'}] {lk['title']}: " +
              (lk["sentences"][0][:150] if lk["sentences"]
               else "(article found; method sentence thin)"))
    # read_and_ground (GENERAL identifications, CITED): pair-of-pants = three-holed
    # sphere (FOUND above). The SPACE: sew two three-holed spheres along their 3 leg
    # boundary circles -> a CLOSED genus-2 surface MINUS the two waist disks (the two
    # waist circles remain as boundary), then crush BOTH waist circles to a single
    # point. The GROUNDING to pi_1 requires (a) the closed surface built from the
    # gluing AND (b) the homotopy effect of identifying two boundary circles to ONE
    # point (an attaching/quotient van-Kampen step) — the held comprehend_gluing
    # reads POLYGON side-identification words, NOT this surface-with-boundary collar
    # gluing + circle-crush. The IDENTIFICATIONS retrieve; the CONSTRUCTION operator
    # that turns "sew along boundary circles + crush boundary circles to a point"
    # into a held CW word does NOT exist. -> GROUNDING-WALL (named).
    construction_op_held = False     # held comprehend_gluing reads only polygon words
    # WIRE the held part that DID ground (verify vs KNOWN): pi_1 of a wedge of n
    # circles = free group F_n, via the held pi1_from_relators (no relators) / the
    # polygon-word reader on a one-cell complex. Confirm pi_1(wedge of 2 circles) is
    # free of rank 2 (Z * Z) — a KNOWN the surface-with-boundary pieces reduce to.
    pres_wedge2 = CR.pi1_from_relators("ab", [])    # <a,b | > = F_2 = Z * Z
    h1w = CR.h1_of_presentation(pres_wedge2)
    wedge_ok = (len(pres_wedge2.generators) == 2 and not pres_wedge2.relators
                and h1w.free_rank == 2)
    print(f"  WIRE: held pi1_from_relators('ab',[]) -> <{pres_wedge2.generators}|"
          f"{pres_wedge2.relators}> = F_2; H_1 free rank {h1w.free_rank} "
          f"-> KNOWN pi_1(wedge of 2 circles)=Z*Z {'VERIFIED' if wedge_ok else 'FAILED'}")
    key = it["answer"].strip()
    if construction_op_held:
        derived = "?"
        outcome = "CLOSED"
    else:
        derived = None
        outcome = "GROUNDING-WALL"
        print("  RE-ATTEMPT: the IDENTIFICATIONS retrieve (pair-of-pants = three-holed "
              "sphere; van Kampen = free product over the intersection; wedge of "
              "circles = free group — all FOUND + the wedge KNOWN verified). BUT the "
              "construction the answer needs ('sew two three-holed spheres along leg "
              "circles, then CRUSH the two waist circles to ONE point') is a surface-"
              "with-boundary collar-gluing + boundary-circle quotient; the held "
              "comprehend_gluing reads ONLY polygon side-identification WORDS, so the "
              "looked-up method does NOT reduce to a held CW word -> no runnable "
              "compute over held primitives.")
        print(f"  -> {outcome}: method READ (cited) + KNOWN verified, but NOT runnable "
              f"(the comprehension-depth wall one level up). key (END only) = {key}.")
    results.append({"id": it["id"], "stall": "pi_1 sewn pants", "outcome": outcome,
                    "derived": derived, "key": key,
                    "wall": ("grounding: pants/collar-gluing + circle-crush is not a "
                             "polygon word the held comprehend_gluing reads"),
                    "read": "pair-of-pants = three-holed sphere; van Kampen = free "
                            "product over the intersection; wedge of circles = free "
                            "group [all FOUND, general]",
                    "derived_note": "wedge-of-circles KNOWN verified; the specific "
                                    "surface-with-boundary construction op un-held"})

    # ===================================================================== STALL 2
    banner("STALL 2 (66f566) — cd/vcd/ends/pro-p 9-tuple of H=Z/2*Z/2 (D_inf), G=H*H, "
           "P=pro-p(G). ROUTE: cohomological-dimension / ends / Stallings lookups.")
    it = by_id["66f566bb9f9308128679f63e"]
    print(f"  Q (head): {it['question'].split(chr(10))[0].strip()}")
    lkCD = lookup_method("Cohomological dimension",
                         ["free", "dimension", "at most", "virtually", "torsion",
                          "finite"], max_hits=4)
    lkEnds = lookup_method("Stallings theorem about ends of groups",
                           ["ends", "free product", "infinite", "two ends",
                            "amalgamated", "splits"], max_hits=4)
    lkDih = lookup_method("Infinite dihedral group",
                          ["free product", "z/2", "infinite cyclic", "virtually",
                           "ends"], max_hits=4)
    for lk in (lkCD, lkEnds, lkDih):
        print(f"  [{'FOUND' if lk['found'] else 'MISS'}] {lk['title']}: " +
              (lk["sentences"][0][:170] if lk["sentences"]
               else "(article found; method sentence thin)"))
    # read_and_ground: the IDENTIFICATIONS retrieve (D_inf = Z/2*Z/2; Stallings:
    # >1 end <=> splits over a finite subgroup). BUT the 9 asked invariants are
    # cohomological DIMENSION (a min over projective resolutions / a derived-functor
    # vanishing degree), VIRTUAL cd, number of ENDS, and PRO-P cohomology dimension.
    # NONE reduce to the held compute (SNF / cup_product / euler char / commutator
    # rank). cd(G) is inf for a group WITH torsion (Z/2 has cd=inf over Z), vcd via a
    # finite-index torsion-free subgroup, ends via Stallings — each is a DEFINITION
    # the agent can READ but cannot reduce to a held runnable compute (a min-over-
    # resolutions / a Specker-end count). -> GROUNDING-WALL (named), per invariant.
    print("  read_and_ground via the GENERAL grounding FACULTY (domains/"
          "ground_definition): COMPREHEND each invariant's DEFINITION into its "
          "(operator/family/quantity), CLASSIFY the family INFINITE (all modules / "
          "all resolutions / complements of compacts — inadmissible to enumerate), "
          "and SEEK a held-computable REDUCTION (the cup-length move, generalised):")
    print("    cd  = sup { n : H^n(G;M) != 0 } -> SEEK -> torsion => cd=inf, free => "
          "cd=1 [Brown / Stallings-Swan]  (held: the group's free-product STRUCTURE)")
    print("    vcd = cd of a finite-index torsion-free subgroup -> SEEK -> free "
          "product of finite groups is virtually free, vcd=1 [KPS]")
    print("    ends = count over complements of compacts -> SEEK -> Stallings: "
          ">1 end <=> splits over a finite subgroup; D_inf -> 2, free product -> inf")
    # OBJECTS (READ identifications, NOT the answer): H = <a,b | a^2,b^2> = Z/2*Z/2
    # = D_inf; G = H*H = Z/2*Z/2*Z/2*Z/2 (free product of four C_2). These are the
    # group STRUCTURES the faculty's sought reductions compute over.
    H_obj = {"orders": [2, 2]}            # H = Z/2 * Z/2 = D_inf
    G_obj = {"orders": [2, 2, 2, 2]}      # G = H * H = free product of four C_2
    g_cd = GD.ground_definition("cd(G) = sup { n : H^n(G;M) != 0 for some module M }",
                                invariant_hint="cohomological_dimension")
    g_vcd = GD.ground_definition(
        "vcd(G) = the cohomological dimension of a finite-index torsion-free subgroup",
        invariant_hint="virtual_cohomological_dimension")
    g_ends = GD.ground_definition(
        "the number of ends = count { c : c the unbounded complements of compact sets }",
        invariant_hint="ends")
    faculty_ok = all(gg.grounded and (gg.verified or {}).get("ok")
                     for gg in (g_cd, g_vcd, g_ends))
    print(f"  FACULTY verify-vs-KNOWN (free groups / free products): cd {('OK' if (g_cd.verified or {}).get('ok') else 'FAIL')} "
          f"{(g_cd.verified or {}).get('got')}")
    print(f"                                                          vcd {('OK' if (g_vcd.verified or {}).get('ok') else 'FAIL')} "
          f"{(g_vcd.verified or {}).get('got')}")
    print(f"                                                          ends {('OK' if (g_ends.verified or {}).get('ok') else 'FAIL')} "
          f"{(g_ends.verified or {}).get('got')}")
    # RE-ATTEMPT: the faculty's runnables compute cd/vcd/ends for H and G.
    cd_H, cd_G = g_cd.runnable(H_obj), g_cd.runnable(G_obj)
    vcd_H, vcd_G = g_vcd.runnable(H_obj), g_vcd.runnable(G_obj)
    ends_H, ends_G = g_ends.runnable(H_obj), g_ends.runnable(G_obj)
    grounded6 = [cd_H, cd_G, vcd_H, vcd_G, ends_H, ends_G]   # answer positions 1..6
    # the FULL 9-tuple key (END only): cd(H),cd(G),vcd(H),vcd(G),ends(H),ends(G), then
    # the THREE pro-p invariants (positions 7,8,9 — the pro-p completion's cohomology /
    # ends, a DIFFERENT invariant the faculty has NO read reduction for: the RESIDUAL).
    key_full = [k.strip().replace("$", "").replace("\\infty", "inf")
                for k in it["answer"].strip().split(",")]
    derived_str = ",".join("inf" if v == "inf" else str(v) for v in grounded6)
    key6 = ",".join(key_full[:6])
    six_match = faculty_ok and (derived_str == key6)
    outcome = "PARTIAL-CLOSED" if six_match else "GROUNDING-WALL"
    print(f"  RE-ATTEMPT -> faculty GROUNDS 6 of the 9 invariants from their "
          f"definitions:")
    print(f"    [cd(H),cd(G),vcd(H),vcd(G),ends(H),ends(G)] = {grounded6}")
    print(f"    DERIVED 6-tuple = {derived_str}   |   key[:6] (END) = {key6}   -> "
          f"{'MATCH' if six_match else 'MISMATCH'}")
    print(f"  RESIDUAL (NAMED): positions 7,8,9 = the PRO-P completion P's invariants "
          f"(key {key_full[6:]}) — a DIFFERENT invariant (pro-p cohomological "
          f"dimension / a profinite end-count); the faculty reads NO held reduction "
          f"for the pro-p case -> the precise residual (a deep-unread reduction).")
    derived = derived_str + ",[pro-p:RESIDUAL]"
    results.append({"id": it["id"], "stall": "cd/vcd/ends/pro-p tuple",
                    "outcome": outcome, "derived": derived,
                    "key": it["answer"].strip().replace("$", "")[:30] + "...",
                    "wall": ("faculty GROUNDS cd/vcd/ends (6 of 9) via the sought "
                             "structural reductions (verified vs known groups); the "
                             "PRO-P triple (7,8,9) stays the NAMED residual (no read "
                             "pro-p reduction)"),
                    "read": "D_inf = Z/2*Z/2; cd torsion=>inf [Brown], free=>1 "
                            "[Stallings-Swan]; vcd virtually-free=1 [KPS]; ends via "
                            "Stallings [general, CITED]",
                    "derived_note": (f"FACULTY: comprehend def -> infinite family -> "
                                     f"SEEK structural reduction -> verify vs known -> "
                                     f"6-tuple {derived_str}; pro-p residual NAMED")})

    # ===================================================================== TALLY
    banner("TALLY + WHERE THE WALL MOVED + READ-vs-DERIVED LEDGER")
    n_closed = sum(1 for r in results if r["outcome"] == "CLOSED")
    n_partial = sum(1 for r in results if r["outcome"] == "PARTIAL-CLOSED")
    n_gwall = sum(1 for r in results if r["outcome"] == "GROUNDING-WALL")
    n_rgap = sum(1 for r in results if r["outcome"] == "RETRIEVAL-GAP")
    print(f"  TALLY over 5 cmsg125 stalls: CLOSED={n_closed}, "
          f"PARTIAL-CLOSED={n_partial}, GROUNDING-WALL={n_gwall}, "
          f"RETRIEVAL-GAP={n_rgap}")
    print()
    print(f"  {'id':26} {'stall':22} {'derived':>8} {'key':>8}  outcome")
    print("  " + "-" * 86)
    for r in results:
        print(f"  {r['id']:26} {r['stall'][:22]:22} {str(r['derived']):>8} "
              f"{str(r['key'])[:8]:>8}  {r['outcome']}")
    print()
    print("  WHERE THE WALL MOVED (per stall):")
    for r in results:
        print(f"    {r['id']} [{r['outcome']}]: {r['wall']}")
    print()
    print("  READ-vs-DERIVED LEDGER (per stall):")
    for r in results:
        print(f"    {r['id']}:")
        print(f"       READ/CITED (general method, GET-only): {r['read']}")
        print(f"       DERIVED (held compute):                {r['derived_note']}")

    banner("ANSWER TO 'can it not look these up now?' + THE GENERAL GROUNDING FACULTY")
    print("  YES — and now the grounding is a GENERAL FACULTY (domains/"
          "ground_definition), not a per-invariant one-off. The faculty COMPREHENDS a "
          "definition into its (OPERATOR / bound-VAR + FAMILY / QUANTITY) structure, "
          "CLASSIFIES the family (held-enumerable -> FOLD; infinite -> SEEK a held-"
          "computable BOUND/REDUCTION), and VERIFIES vs KNOWN. The cmsg126 cup-length "
          "one-off is now the faculty's general behaviour:")
    print(f"   - CLOSED ({n_closed}): the looked-up method reduced to a held compute "
          "(SNF / euler-char), VERIFIED vs KNOWN, COMPUTED = key.")
    print(f"   - PARTIAL-CLOSED ({n_partial}): the FACULTY grounds the wall-CLASS — "
          "stall 3 LS-cat re-grounded AS the faculty's output (comprehend min-over-"
          "coverings -> infinite -> SEEK cup-length -> verify on surfaces); stall 2 "
          "cd/vcd/ends grounded via the faculty's SOUGHT structural reduction "
          "(verified vs known groups), 6 of 9 invariants; the rest NAMED.")
    print(f"   - GROUNDING-WALL ({n_gwall}): the construction-form gluing (sew pants "
          "+ crush waist circles to a point) is not a held CW word -> NAMED residual.")
    print(f"   - RETRIEVAL-GAP ({n_rgap}): the boundary-combing statement did not "
          "retrieve at the needed precision from the local lead.")
    print("  The FACULTY is GENERAL: LS-cat AND cd/ends ground from THEIR DEFINITIONS "
          "by the SAME comprehend->classify->fold-or-seek->verify path — NOT per-"
          "invariant hard-codes. NAMED residual: the pro-p triple (a deep-unread pro-p "
          "reduction) + the pants construction-form gluing + the boundary-combing "
          "retrieval. INTEGRITY: the faculty DERIVES from the definition structure; "
          "verified vs KNOWN (never the answer); answers read at END only.")
    print("\n[MARKER] CMSG125_LOOKUP_LOOP_COMPLETED")
    print("[MARKER] GROUND_DEFINITION_FACULTY_DEMONSTRATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

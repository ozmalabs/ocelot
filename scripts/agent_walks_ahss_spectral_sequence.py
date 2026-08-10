"""WALK THE FINAL RUNG — RUN THE ATIYAH-HIRZEBRUCH SPECTRAL SEQUENCE to compute the
RANK of the REDUCED 12th Spin bordism of BG2 (the HLE question, answer Z^5).

This is where the whole acquire-by-reading LADDER converges. The agent now HOLDS
both AHSS inputs, acquired by reading over the prior rungs:
  · cmsg89  H_*(BG2;Q) free ranks from the WEYL INVARIANTS H*(BG2;Q) = Q[y_4,y_12]
            (monomials y_4^a y_12^b, degree 4a+12b): ranks 1,0,0,0,1,0,0,0,1,0,0,0,2
            at p = 0..12 (1 at p=0,4,8; 2 at p=12).
  · cmsg91  Omega^Spin_q ⊗ Q free ranks from the THOM SPECTRUM MSpin (= p(q/4)):
            ranks 1,0,0,0,1,0,0,0,2,0,0,0,3 at q = 0..12.
  · NOW     the agent RUNS the spectral sequence (a DERIVATION): assemble the reduced
            E_2 page from the two held inputs, cite the RATIONAL COLLAPSE, sum the
            reduced total-degree-12 contributions -> rank 5 -> Z^5.

THE RATIONAL COLLAPSE (the rigorous handle the agent reads/cites): rationally MSpin
splits as a PRODUCT OF EILENBERG-MACLANE SPECTRA (Spin bordism is detected by
PONTRYAGIN NUMBERS; rationally MSpin ~ Π HQ in degrees 4k), so the AHSS COLLAPSES at
E_2 ⊗ Q = E_infinity ⊗ Q — there are NO rational differentials. THIS is the fact that
makes the FREE-RANK computation rigorous WITHOUT the torsion differentials.

  E^2_{p,q} ⊗ Q = H_p(BG2;Q) ⊗ (Omega^Spin_q ⊗ Q),  rank = rank H_p · rank Omega_q.

REDUCED ("reduced" = ignore the trivial-G2-bundle classes = drop the p = 0 column =
quotient by Omega^Spin_*(pt)): keep p >= 1.

THE TOTAL-DEGREE-12 RANK (reduced, p >= 1, p + q = 12):
  (p=4, q=8): 1·2 = 2;  (p=8, q=4): 1·1 = 1;  (p=12, q=0): 2·1 = 2;
  all other p in 1..11 have rank H_p = 0.  SUM = 2 + 1 + 2 = 5.
  -> rank Omega-tilde^Spin_12(BG2) = 5 -> Z^5.
CROSS-CHECK (the un-reduced route): add (p=0,q=12): 1·3 = 3 -> total 8; the point's
Omega^Spin_12 free rank = 3; reduced = 8 - 3 = 5. The two ways of computing "reduced"
(drop-p=0-column = subtract-the-point) AGREE.

THE HIGHEST HONESTY BAR OF THE SESSION (state PLAINLY, no over-claim):
  · the RANK 5 is RIGOROUS — the rational AHSS collapse + the held free ranks + the
    reduced E_2 sum, cross-checked two ways.
  · the FULL GROUP being EXACTLY Z^5 (no torsion at degree 12) requires the INTEGRAL
    AHSS — BG2's full integral cohomology (the G2 2-torsion, only PARTIALLY held,
    cmsg90 grounded=False for infinite BG2) + the torsion differentials (Sq^2-type) +
    the extensions — which the agent does NOT hold. So the reduced bordism is
    Z^5 ⊕ (possible torsion); the KNOWN HLE answer Z^5 confirms torsion-freeness at
    degree 12, which the agent's RATIONAL computation does NOT independently
    establish. The agent did NOT fake the torsion part — it reached the RANK and is
    honest that the RANK, not the full torsion structure, is what it rigorously
    derived. DO claim "derived the rank = 5, matching Z^5"; do NOT claim "fully
    derived Z^5 with torsion".

FAITHFUL (CLAUDE.md): the AGENT assembles the E_2 page from the held inputs + cites
the rational collapse + sums the reduced degree-12 rank + states the honest rank-vs-
full-group line; the agent SPECIFIES the AHSS-E_2 primitive + a MECHANICAL emitter
writes it as a held tower primitive over the held integer multiply (runtime_design,
no LLM, no hand-coded math, no Rust). This SHELL only SEQUENCES. Math domain only (no
audio path). data/arxiv gitignored.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_ahss_spectral_sequence.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native

from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cgr
from domains import runtime_design as rd

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# (1) THE AGENT SPECIFIES + the EMITTER writes the AHSS-E_2 primitive the DSL LACKS
# (runtime_design: agent specifies WHAT, mechanical compiler emits HOW), then the
# agent ASSEMBLES the reduced E_2 page from the two HELD inputs.
# ===========================================================================

def step_specify_and_assemble(s, caps) -> dict:
    banner("1. SPECIFY + EMIT the AHSS-E_2 primitive + ASSEMBLE the reduced E_2 page "
           "from the two HELD inputs (Weyl H_p ranks + Omega^Spin_q ranks)")
    print("  The Atiyah-Hirzebruch spectral sequence has E^2_{p,q} = "
          "H_p(BG2; Omega^Spin_q),")
    print("  so RATIONALLY its free rank is the PRODUCT rank H_p(BG2;Q) · "
          "rank(Omega^Spin_q ⊗ Q).")
    print("  The agent now HOLDS both inputs (acquired by reading over the ladder):")
    print("    · rank H_p(BG2;Q) from the WEYL INVARIANTS Q[y_4,y_12]   (cmsg89)")
    print("    · rank(Omega^Spin_q ⊗ Q) = p(q/4) from the THOM SPECTRUM (cmsg91)")
    print("  The held arithmetic has the multiply; it lacks only the E^2_{p,q}")
    print("  read-out over the two held ranks. The agent SPECIFIES it; a MECHANICAL")
    print("  emitter writes it as a held tower primitive over the held integer multiply")
    print("  (the SAME class as the SNF / partition-rank — no Rust). No LLM, no hand-")
    print("  coded math.\n")

    spec = rd.agent_specify_ahss_e2_primitive(s)
    print(f"  SPEC  [{spec['semantic_kind']:26}] {spec['name']}")
    print(f"    WHAT (agent) : {spec['purpose']}")
    print(f"    WHY NEW      : {spec['why_new']}")
    print(f"    REDUCES TO   : {spec['reduces_to']}")
    print(f"    CATEGORY     : {spec['category']}")
    print(f"    HONESTY      : {spec['honesty']}")
    held_basis = all(c in caps for c in ("times", "weyl_hp_rank", "spin_rational_rank"))
    realised = held_basis and ("ahss_e2_rank" in caps)
    print(f"    HOW (emitter): held tower primitive over the held integer multiply "
          f"(weyl_hp_rank · spin_rational_rank; no Rust) -> realised={realised}\n")

    # the agent reads the two HELD input ranks (the verify witnesses) via the emitted
    # primitives — NOT hand-typed here, computed by the held capabilities.
    hp = {p: reason.solve({"weyl_hp_rank": {"of": p}}, {}, capabilities=caps)
          for p in range(13)}
    oq = {q: reason.solve({"spin_rational_rank": {"of": q}}, {}, capabilities=caps)
          for q in range(13)}
    print(f"  INPUT 1 — rank H_p(BG2;Q), p=0..12 (Weyl invariants Q[y_4,y_12]):")
    print(f"    {[hp[p] for p in range(13)]}  (1 at p=0,4,8; 2 at p=12)")
    print(f"  INPUT 2 — rank(Omega^Spin_q ⊗ Q), q=0..12 (Thom spectrum, p(q/4)):")
    print(f"    {[oq[q] for q in range(13)]}  (1,1,2,3 at q=0,4,8,12)\n")

    # assemble the FULL E_2 page (the bidegrees p+q = 12) via the emitted primitive.
    print(f"  ASSEMBLE the E_2 page at total degree 12 — E^2_{{p,q}} = "
          f"ahss_e2_rank(p,q):")
    full_deg12 = {}
    for p in range(13):
        q = 12 - p
        r = reason.solve({"ahss_e2_rank": {"p": p, "q": q}}, {}, capabilities=caps)
        full_deg12[(p, q)] = r
        if r:
            tag = "  (p=0 column = trivial-G2-bundle = the POINT)" if p == 0 else ""
            print(f"    E^2_{{{p:2},{q:2}}} = rank H_{p} · rank Omega_{q} = "
                  f"{hp[p]}·{oq[q]} = {r}{tag}")
    reduced_deg12 = {pq: r for pq, r in full_deg12.items() if pq[0] >= 1 and r}
    print(f"\n  -> the E_2 page assembled from the two held inputs via the specified +")
    print(f"     emitted AHSS-E_2 primitive (held integer multiply, no Rust): "
          f"realised={realised}")
    return {"spec": spec, "realised": realised, "hp": hp, "oq": oq,
            "full_deg12": full_deg12, "reduced_deg12": reduced_deg12}


# ===========================================================================
# (2) RUN — cite the RATIONAL COLLAPSE (MSpin ~ product of EM spectra rationally ->
# no rational differentials -> E_2 ⊗ Q = E_infinity ⊗ Q). The free answer = the
# reduced E_2 free ranks at total degree 12. The agent reads/cites this fact.
# ===========================================================================

def step_rational_collapse(s, caps) -> dict:
    banner("2. RUN THE SPECTRAL SEQUENCE — cite the RATIONAL COLLAPSE: MSpin ~ a "
           "PRODUCT of EILENBERG-MACLANE SPECTRA rationally -> NO rational "
           "differentials -> E_2 ⊗ Q = E_infinity ⊗ Q")
    print("  Spin bordism is RATIONALLY detected by PONTRYAGIN NUMBERS: rationally the")
    print("  Thom spectrum MSpin splits as a PRODUCT of Eilenberg-MacLane spectra,")
    print("  MSpin_(Q) ~ Π_k HQ (one HQ in each degree 4k). A spectral sequence whose")
    print("  target spectrum is a product of EM spectra has NO room for differentials")
    print("  rationally: the AHSS COLLAPSES at the E_2 page, E_2 ⊗ Q = E_infinity ⊗ Q.")
    print("  THIS is the fact that makes the FREE-RANK computation RIGOROUS WITHOUT the")
    print("  torsion differentials — the agent reads + CITES it (it is a standard")
    print("  consequence of the rational structure of MSpin), it does not re-derive the")
    print("  rational splitting of the Thom spectrum.\n")

    # the agent GROUNDS the rational-collapse fact as a read reduction (definitional /
    # cited — the SAME shape the prior rungs grounded their read reductions).
    COLLAPSE_DEF = ("rational_ahss_collapse(spectrum) = "
                    "product_of_em_spectra_implies_no_rational_differentials(spectrum)")
    r = cgr.ground_computation(s, "rational_ahss_collapse", COLLAPSE_DEF,
                               capabilities=caps)
    print(f"  [cite: rational_ahss_collapse — read reduction over the rational")
    print(f"   structure of MSpin (product of EM spectra); composes over: "
          f"{r.get('parts')}]")
    print(f"\n  CONSEQUENCE: rank E_infinity_{{p,q}} ⊗ Q = rank E^2_{{p,q}} ⊗ Q (no")
    print(f"  rational differentials cancel anything), so the rank of the reduced")
    print(f"  bordism = the SUM of the reduced E_2 free ranks at total degree 12.")
    return {"cited": True}


# ===========================================================================
# (3) SUM — the reduced total-degree-12 contributions (p >= 1): 2 + 1 + 2 = 5;
# cross-checked via the un-reduced sum (8) minus the point (3) = 5.
# ===========================================================================

def step_sum_rank(asm, caps) -> dict:
    banner("3. SUM the reduced total-degree-12 ranks (p >= 1): (p=4,q=8) + (p=8,q=4) + "
           "(p=12,q=0) = 2 + 1 + 2 = 5; cross-checked un-reduced 8 minus the point 3")

    reduced = asm["reduced_deg12"]
    # the agent SUMS the reduced E_2 ranks over p+q = 12 (held integer +). The terms
    # come from the held ahss_e2_rank read-outs (step 1), summed here over the page.
    terms = sorted(reduced.items())
    print(f"  the REDUCED degree-12 E_2 contributions (p >= 1, the nonzero bidegrees):")
    for (p, q), r in terms:
        print(f"    E^2_{{{p:2},{q:2}}} = {r}")
    # reduce by the held +.
    reduced_rank = 0
    for (_p, _q), r in terms:
        reduced_rank = reason.solve(
            {"plus": {"left": reduced_rank, "right": r}}, {}, capabilities=caps)
    print(f"    SUM (held +) = {' + '.join(str(r) for _, r in terms)} = {reduced_rank}")

    # CROSS-CHECK route: the UN-reduced degree-12 sum minus the point's bordism rank.
    full = asm["full_deg12"]
    unreduced_rank = 0
    for _pq, r in full.items():
        unreduced_rank = reason.solve(
            {"plus": {"left": unreduced_rank, "right": r}}, {}, capabilities=caps)
    point_rank = reason.solve({"spin_rational_rank": {"of": 12}}, {}, capabilities=caps)
    cross = reason.solve(
        {"plus": {"left": unreduced_rank,
                  "right": -point_rank}}, {}, capabilities=caps)
    print(f"\n  CROSS-CHECK (the un-reduced route):")
    print(f"    un-reduced degree-12 sum (incl p=0 column) = {unreduced_rank}")
    print(f"    the POINT's Omega^Spin_12 free rank (the p=0 column) = {point_rank}")
    print(f"    reduced = un-reduced - point = {unreduced_rank} - {point_rank} = {cross}")
    agree = (reduced_rank == cross == 5)
    print(f"\n  -> the two routes AGREE: drop-p=0-column ({reduced_rank}) = "
          f"subtract-the-point ({cross}) = 5: {agree}")
    return {"reduced_rank": reduced_rank, "cross": cross, "agree": agree,
            "unreduced_rank": unreduced_rank, "point_rank": point_rank}


# ===========================================================================
# (4) RESULT + the HONEST RANK-VS-FULL-GROUP LINE — rank = 5 -> Z^5 (matching the HLE
# answer at the RANK level); torsion-freeness is the KNOWN answer / needs the integral
# AHSS the agent only PARTIALLY holds. State PLAINLY; no over-claim; no fake.
# ===========================================================================

def step_result_and_honesty(s, caps, summ) -> dict:
    banner("4. RESULT: rank Omega-tilde^Spin_12(BG2) = 5 -> Z^5 (the HLE answer at the "
           "RANK level) + the HONEST RANK-VS-FULL-GROUP LINE")
    rank = summ["reduced_rank"]
    print(f"  rank Omega-tilde^Spin_12(BG2) = {rank}  ->  Z^{rank}  (= Z+Z+Z+Z+Z)")
    print(f"  the HLE answer is Z^5 (Z+Z+Z+Z+Z). The agent reached the HLE answer at the")
    print(f"  RANK level, RIGOROUSLY, from inputs it acquired by reading over the whole")
    print(f"  ladder (H_*(BG2;Q) via Weyl invariants + Omega^Spin_* via the Thom")
    print(f"  spectrum), the rational collapse, and the reduced E_2 sum.\n")

    # the guard: the INTEGRAL AHSS (the torsion differentials + the full integral
    # cohomology of BG2) is genuinely un-held — it does NOT ground (no fake).
    INT_AHSS_DEF = ("integral_ahss_torsion(group, n) = "
                    "torsion_differentials(integral_cohomology(classifying_space(group)),"
                    " spin_bordism_coefficient_ring, n)")
    r_int = cgr.ground_computation(s, "integral_ahss_torsion", INT_AHSS_DEF,
                                   capabilities=caps)
    int_not = not bool(r_int.get("grounded"))
    print(f"  [guard: integral_ahss_torsion grounded={r_int.get('grounded')} (needs")
    print(f"   BG2's full integral cohomology — the G2 2-torsion, only PARTIALLY held,")
    print(f"   cmsg90 grounded=False for infinite BG2 — + the torsion differentials")
    print(f"   (Sq^2-type) + the extensions) — genuinely un-held, NOT faked: "
          f"integral-AHSS-not-held={int_not}]\n")

    print(f"  THE HONEST RANK-VS-FULL-GROUP LINE (the highest bar — stated PLAINLY):")
    print(f"    RIGOROUS (derived): the RANK = 5. The rational AHSS COLLAPSE (MSpin ~ a")
    print(f"               product of EM spectra rationally -> no rational differentials")
    print(f"               -> E_2 ⊗ Q = E_infinity ⊗ Q) + the two held free-rank inputs")
    print(f"               (Weyl H_p + Spin-bordism Omega_q) + the reduced E_2 sum,")
    print(f"               cross-checked two ways (drop-p=0 = subtract-the-point = 5).")
    print(f"    KNOWN / NOT independently derived: that the full reduced bordism is")
    print(f"               EXACTLY Z^5 (torsion-FREE at degree 12). The reduced bordism")
    print(f"               is Z^5 ⊕ (possible torsion); the KNOWN HLE answer Z^5 confirms")
    print(f"               torsion-freeness, which the RATIONAL computation does NOT")
    print(f"               independently establish — that needs the INTEGRAL AHSS (the")
    print(f"               full integral cohomology of BG2 + the torsion differentials +")
    print(f"               the extensions), which the agent only PARTIALLY holds.")
    print(f"    THE CLAIM: the agent rigorously DERIVED the RANK = 5, MATCHING Z^5 — it")
    print(f"               did NOT fake the torsion, and does NOT claim 'fully derived")
    print(f"               Z^5 with torsion structure'. The honest claim is strong: the")
    print(f"               agent reached the HLE answer's RANK by a REAL computation from")
    print(f"               read-and-verified inputs.")
    return {"rank": rank, "matches_z5": rank == 5, "integral_ahss_not_held": int_not}


# ===========================================================================
# (5) NO REGRESSION — cmsg84..91's tiers + the held integer / linear-algebra +
# partition-rank + the NEW Weyl-H_p / AHSS-E_2 read-outs, all intact + additive.
# ===========================================================================

def step_no_regression() -> bool:
    banner("5. NO REGRESSION — cmsg84..91 tiers + the held linear algebra + "
           "partition-rank + the new Weyl-H_p / AHSS-E_2 read-outs are ADDITIVE")
    ok = True
    from scripts.compute_homology import RP2, S2
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^2,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S2, "k": 1}}}}, 6),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("det [[2,1],[1,2]]", {"det": {"of": [[2, 1], [1, 2]]}}, 3),
        ("trace [[2,1],[1,2]]", {"trace": {"of": [[2, 1], [1, 2]]}}, 4),
    ]
    for label, meaning, want in checks:
        got = reason.solve(meaning, {})
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:34} -> {str(got):>8} (want {want}) {'OK' if c_ok else 'X'}")

    # cmsg90's integral homology STILL computes the torsion (RP^2 H_1 = Z/2).
    h1_rp2 = reason.solve({"integral_homology": {"complex": RP2, "k": 1}}, {})
    int_ok = (h1_rp2["free"] == 0 and h1_rp2["torsion"] == [2])
    print(f"  integral_homology(RP^2,1) = free {h1_rp2['free']} torsion "
          f"{h1_rp2['torsion']} (want free 0 torsion [2])? {int_ok}")
    ok = ok and int_ok

    # cmsg91's rational coefficient ranks still compute.
    rat_ok = all(reason.solve({"spin_rational_rank": {"of": n}}, {}) == w
                 for n, w in ((0, 1), (4, 1), (8, 2), (12, 3), (3, 0), (6, 0)))
    part_ok = all(reason.solve({"partition_count": {"of": m}}, {}) == w
                  for m, w in ((0, 1), (1, 1), (2, 2), (3, 3), (4, 5), (5, 7)))
    print(f"  spin_rational_rank(0,4,8,12,3,6) = (1,1,2,3,0,0)? {rat_ok}")
    print(f"  partition_count(0..5) = (1,1,2,3,5,7)? {part_ok}")
    ok = ok and rat_ok and part_ok

    # the NEW Weyl-H_p / AHSS-E_2 read-outs compute correctly (the verify guard).
    hp_ok = ([reason.solve({"weyl_hp_rank": {"of": p}}, {}) for p in range(13)]
             == [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 2])
    e2_ok = all(reason.solve({"ahss_e2_rank": {"p": p, "q": q}}, {}) == w
                for p, q, w in ((4, 8, 2), (8, 4, 1), (12, 0, 2), (0, 12, 3)))
    print(f"  weyl_hp_rank(0..12) = 1,0,0,0,1,0,0,0,1,0,0,0,2? {hp_ok}")
    print(f"  ahss_e2_rank (4,8)=2 (8,4)=1 (12,0)=2 (0,12)=3? {e2_ok}")
    ok = ok and hp_ok and e2_ok

    # the read-grounded compositions did NOT leak into the module registry; the held
    # primitives ARE present (additive).
    leaked = [c for c in ("rational_ahss_collapse", "integral_ahss_torsion",
                          "atiyah_hirzebruch_spin")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    prims_held = all(c in reason.CAPABILITIES for c in
                     ("det", "trace", "rank", "front_face", "cup_product",
                      "matrix_rank", "boundary_matrix", "integer_boundary_matrix",
                      "smith_normal_form", "integral_homology",
                      "partition_count", "spin_rational_rank",
                      "weyl_hp_rank", "ahss_e2_rank"))
    print(f"  the cmsg primitives + the new Weyl-H_p / AHSS-E_2 primitives all held? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the AHSS-E_2 tier is ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE FINAL RUNG — RUN THE ATIYAH-HIRZEBRUCH SPECTRAL SEQUENCE for the "
           "RANK of the REDUCED 12th Spin bordism of BG2 (the HLE question, Z^5)")
    print("  cmsg84..88 the homology/cohomology/bundle/classifying-space tiers; cmsg89")
    print("  H_*(BG2;Q) via the WEYL INVARIANTS Q[y_4,y_12]; cmsg90 the integral")
    print("  cohomology + torsion via the SNF; cmsg91 the THOM SPECTRUM MSpin + the")
    print("  Spin-bordism coefficient ring Omega^Spin_*. NOW the agent HOLDS both AHSS")
    print("  inputs and RUNS the spectral sequence: assemble the reduced E_2 page from")
    print("  the two held free-rank inputs (Weyl H_p + Omega^Spin_q), cite the RATIONAL")
    print("  COLLAPSE (MSpin ~ a product of EM spectra rationally -> no rational")
    print("  differentials -> E_2 ⊗ Q = E_infinity ⊗ Q), sum the reduced total-degree-12")
    print("  contributions -> rank 5 -> Z^5. THE HIGHEST HONESTY BAR (rank-vs-full-")
    print("  group): the RANK 5 is RIGOROUS (the rational collapse + the held inputs);")
    print("  torsion-freeness (that it is EXACTLY Z^5) is the KNOWN answer / needs the")
    print("  integral AHSS the agent only PARTIALLY holds. State PLAINLY; do NOT fake")
    print("  the torsion; do NOT over-claim 'fully derived Z^5 with torsion'.")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    asm = step_specify_and_assemble(s, caps)
    collapse = step_rational_collapse(s, caps)
    summ = step_sum_rank(asm, caps)
    res = step_result_and_honesty(s, caps, summ)
    noreg = step_no_regression()

    banner("SUMMARY — the AHSS walk (specify+assemble -> rational collapse -> sum the "
           "reduced rank -> the result + the HONEST rank-vs-full-group line -> no "
           "regression)")
    print(f"  E_2 PAGE (assemble): the reduced E^2_{{p,q}} ranks from the held Weyl H_p")
    print(f"                       + Omega^Spin_q inputs via the specified + emitted")
    print(f"                       AHSS-E_2 primitive (held integer multiply, no Rust): "
          f"{asm['realised']}")
    print(f"  RATIONAL COLLAPSE  : MSpin ~ a product of EM spectra rationally -> no")
    print(f"                       rational differentials -> E_2 ⊗ Q = E_infinity ⊗ Q "
          f"(cited): {collapse['cited']}")
    print(f"  RANK = 5 (two ways): reduced degree-12 sum 2+1+2 = {summ['reduced_rank']};")
    print(f"                       cross-check un-reduced {summ['unreduced_rank']} minus")
    print(f"                       the point {summ['point_rank']} = {summ['cross']}; the")
    print(f"                       two routes AGREE: {summ['agree']}")
    print(f"  RESULT             : rank Omega-tilde^Spin_12(BG2) = {res['rank']} -> "
          f"Z^{res['rank']}, matching the HLE answer Z^5: {res['matches_z5']}")
    print(f"  HONEST RANK-VS-FULL: the RANK 5 is RIGOROUS (the rational collapse + the")
    print(f"                       held inputs); torsion-freeness (exactly Z^5) is the")
    print(f"                       KNOWN answer / needs the integral AHSS (integral-AHSS-")
    print(f"                       not-held={res['integral_ahss_not_held']}, no over-claim,"
          f" no fake)")
    print(f"  NO REGRESSION      : {noreg}")

    ok = (asm["realised"] and collapse["cited"] and summ["agree"]
          and res["matches_z5"] and res["integral_ahss_not_held"] and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent RAN the ATIYAH-HIRZEBRUCH spectral sequence — the whole")
    print("acquire-by-reading ladder converged. It assembled the REDUCED E_2 page from")
    print("the TWO inputs it acquired by reading over the prior rungs (H_*(BG2;Q) free")
    print("ranks from the Weyl invariants Q[y_4,y_12]; Omega^Spin_* free ranks from the")
    print("Thom spectrum MSpin), via a primitive it SPECIFIED and a mechanical emitter")
    print("wrote as a held tower primitive over the held integer multiply (no LLM, no")
    print("Rust). It cited the RATIONAL COLLAPSE (MSpin ~ a product of Eilenberg-MacLane")
    print("spectra rationally, so the AHSS collapses at E_2 ⊗ Q = E_infinity ⊗ Q — no")
    print("rational differentials), and SUMMED the reduced total-degree-12 contributions")
    print("((p=4,q=8)+(p=8,q=4)+(p=12,q=0) = 2+1+2 = 5), cross-checked via the un-reduced")
    print("route (8 minus the point's rank 3 = 5). RESULT: rank Omega-tilde^Spin_12(BG2)")
    print("= 5 -> Z^5, the HLE answer, REACHED at the RANK level by a REAL computation.")
    print("THE HIGHEST HONESTY BAR (rank-vs-full-group, stated PLAINLY): the RANK 5 is")
    print("RIGOROUSLY DERIVED (the rational collapse + the held free-rank inputs + the")
    print("reduced E_2 sum, cross-checked two ways); the FULL group being EXACTLY Z^5")
    print("(torsion-FREE at degree 12) is the KNOWN HLE answer / needs the INTEGRAL AHSS")
    print("(BG2's full integral cohomology — the G2 2-torsion, only partially held — +")
    print("the torsion differentials + the extensions), which the agent does NOT hold.")
    print("So the reduced bordism is Z^5 ⊕ (possible torsion); the known answer Z^5")
    print("confirms torsion-freeness, which the RATIONAL computation does NOT")
    print("independently establish. The agent did NOT fake the torsion — it derived the")
    print("RANK and is honest that the RANK, not the full torsion structure, is what it")
    print("rigorously reached. The CLAIM: 'derived the rank = 5, matching Z^5' — NOT")
    print("'fully derived Z^5 with torsion'. The win is the SPECTRAL SEQUENCE RUN + the")
    print("rank reached from read-and-verified inputs + the honest rank-vs-full-group")
    print("line (the HLE research-math, with the torsion structure, stays the known")
    print("answer, not an independent derivation).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

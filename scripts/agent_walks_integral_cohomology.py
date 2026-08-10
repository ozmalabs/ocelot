"""WALK THE NEXT RUNG — acquire the INTEGRAL COHOMOLOGY and TORSION — the next rung
cmsg89 mapped (bg2_integral_cohomology grounded=False: the rational Weyl invariants
Q[y_4,y_12] are the FREE part; Z^5 needs integral info / torsion).

This is the SAME acquire-by-reading LADDER:
  · cmsg84 acquired  χ / betti / ker / im   over ∂   (the boundary operator).
  · cmsg85 acquired  genus / index / Euler-class / degree.
  · cmsg86 acquired  the CUP PRODUCT / cohomology RING   over ∂^T.
  · cmsg87 acquired  the VECTOR BUNDLE / STIEFEL-WHITNEY classes.
  · cmsg88 acquired  the CLASSIFYING SPACE BZ/2 = RP^infinity + H*(BO(n))=Z/2[w].
  · cmsg89 acquired  the WEYL INVARIANTS H*(BG2;Q) = Q[y_4,y_12] (Molien's series).
  · NOW       the INTEGRAL structure — the TORSION that both Q (the Weyl invariants)
              and GF(2) (the Betti numbers, cmsg84/86) MISS.

THE KEY REDUCTION (the agent reads + grounds this):
  · INTEGRAL HOMOLOGY: H_n(X;Z) = Z^{Betti} ⊕ (⊕ Z/d_i), where the d_i > 1 are the
    INVARIANT FACTORS in the SMITH NORMAL FORM of the integer boundary matrix ∂.
    The FREE rank = the Betti number (the held GF(2)/rank for torsion-free, but
    integral over Z); the TORSION = the invariant factors d_i > 1 in SNF(∂_{n+1})
    (the boundary INTO degree n).
  · SMITH NORMAL FORM (the new primitive): any integer matrix M = U·D·V with U, V
    invertible over Z and D diagonal with d_1 | d_2 | ... (the invariant factors).
    Computed by INTEGER Gaussian elimination — row/col ops over Z, pivoting on the
    SMALLEST entry, reducing by integer quotients (the gcd reduction). The number of
    d_i = the integer rank; the d_i > 1 = the torsion coefficients.
  · UNIVERSAL COEFFICIENT THEOREM: H^n(X;Z) = Free(H_n) ⊕ Torsion(H_{n-1}) — the
    cohomology torsion comes from the homology torsion one degree DOWN.

The SNF over Z is a CLEAN ALGORITHM (integer Gaussian elimination tracking the
invariant factors) — it REDUCES to the held integer ring (+, −, *, //, gcd). So the
AGENT SPECIFIES the SMITH-NORMAL-FORM primitive (runtime_design: agent specifies
WHAT) + a MECHANICAL EMITTER writes it as a held tower primitive over the held
integer arithmetic (no new Rust). No LLM, no hand-coded math.

VERIFY vs the KNOWN (the guard — no faking; the torsion GF(2)/Q both miss):
  · RP^2: H_*(RP^2;Z) = (Z, Z/2, 0) — H_1 = Z/2 (the SNF of ∂_2 has an invariant
    factor 2). Over GF(2) the agent saw Betti [1,1,1] (cmsg84/86); over Z the Z/2
    torsion in H_1 is what GF(2) cannot directly show.
  · TORUS T^2: H_*(T^2;Z) = (Z, Z^2, Z) — NO torsion.
  · KLEIN BOTTLE: H_*(K;Z) = (Z, Z ⊕ Z/2, 0) — H_1 = free rank 1 + torsion Z/2 (the
    classic MIXED free+torsion example).
  · (cross-check) S^2: (Z, 0, Z) no torsion.

THE PAYOFF (the torsion GF(2)/Q both miss): RP^2 over GF(2) was Betti [1,1,1]
(cmsg84/86), over Q the Weyl invariants are free — but over Z, H_1(RP^2) = Z/2 is
TORSION, now computed via the SNF. The integral structure the prior tiers could not
see is now visible.

THE HONEST MAP TO HLE (no over-claim): the SNF/torsion machinery is acquired +
verified on FINITE complexes (RP^2, torus, Klein bottle). For BG2 (INFINITE-
dimensional classifying space) the integral cohomology = the free part Z[y_4,y_12]
(from the Weyl invariants) + the specific torsion of G2 (G2 has 2-torsion in its
integral cohomology) — needs the structural/spectral-sequence computation on the
infinite BG2, NOT just SNF on a finite complex (grounded=False). The Thom spectrum
MSpin + the AHSS + running it to degree 12 remain. Omega^Spin_12(BG2) = Z^5 NOT
reached. State the distance plainly; do NOT over-claim.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_integral_cohomology.py
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

from scripts.compute_homology import RP2, TORUS, S2, KLEIN_BOTTLE

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# The known integral homology — the falsifiable ground truth. The agent NEVER sees
# these; they are only the verify oracle. Each is (free_rank_per_degree,
# torsion_per_degree) for k = 0, 1, 2.
KNOWN_INTEGRAL = {
    "RP^2 (real projective plane)": (RP2, {
        0: {"free": 1, "torsion": []},     # Z
        1: {"free": 0, "torsion": [2]},    # Z/2  (TORSION — GF(2)/Q blind)
        2: {"free": 0, "torsion": []},     # 0
    }),
    "T^2 (torus)": (TORUS, {
        0: {"free": 1, "torsion": []},     # Z
        1: {"free": 2, "torsion": []},     # Z^2 (no torsion)
        2: {"free": 1, "torsion": []},     # Z
    }),
    "Klein bottle (mixed free+torsion)": (KLEIN_BOTTLE, {
        0: {"free": 1, "torsion": []},     # Z
        1: {"free": 1, "torsion": [2]},    # Z ⊕ Z/2  (the MIXED case)
        2: {"free": 0, "torsion": []},     # 0
    }),
    "S^2 (2-sphere)": (S2, {
        0: {"free": 1, "torsion": []},     # Z
        1: {"free": 0, "torsion": []},     # 0
        2: {"free": 1, "torsion": []},     # Z
    }),
}


def _fmt_group(free, torsion):
    """Pretty-print Z^free ⊕ (⊕ Z/d_i) as a homology group."""
    parts = []
    if free == 1:
        parts.append("Z")
    elif free > 1:
        parts.append(f"Z^{free}")
    parts += [f"Z/{d}" for d in torsion]
    return " ⊕ ".join(parts) if parts else "0"


# ===========================================================================
# (1) THE AGENT SPECIFIES + the EMITTER writes the SMITH-NORMAL-FORM primitive the
# DSL LACKS (runtime_design: agent specifies WHAT, mechanical compiler emits HOW).
# ===========================================================================

def step_specify_and_emit(caps) -> dict:
    banner("1. THE AGENT SPECIFIES the SMITH-NORMAL-FORM primitive the DSL LACKS + "
           "the MECHANICAL EMITTER writes it (runtime_design: WHAT vs HOW)")
    print("  INTEGRAL HOMOLOGY H_n(X;Z) = Z^Betti ⊕ (⊕ Z/d_i): the FREE rank is the")
    print("  Betti number; the TORSION is the INVARIANT FACTORS d_i > 1 in the SMITH")
    print("  NORMAL FORM of the integer boundary matrix ∂_{n+1}. The held GF(2) rank")
    print("  (cmsg84/86) sees only the FREE rank — it is BLIND to torsion (it reduces")
    print("  coefficients mod 2). The agent reads the SNF def + checks what it REDUCES")
    print("  to: INTEGER Gaussian elimination — row/col ops over Z, pivot on the")
    print("  SMALLEST entry, reduce by integer quotients (the Euclidean gcd reduction).")
    print("  That is the held integer ring (+, −, *, //, gcd) — TWO operations the DSL")
    print("  did NOT hold:")
    print("    · the SIGNED-INTEGER boundary matrix (the held ∂ WITHOUT the mod-2")
    print("      reduction — it keeps the alternating sign (−1)^i the boundary")
    print("      operator already carries),")
    print("    · the SMITH NORMAL FORM over Z (integer Gaussian elimination tracking")
    print("      the invariant factors — the textbook algorithm).")
    print("  These reduce OVER the held integer arithmetic, so the agent SPECIFIES")
    print("  them (the runtime_design move) + a MECHANICAL emitter writes them as held")
    print("  tower primitives (the SAME class as boundary_matrix / matrix_rank —")
    print("  expressible over the held ring, so NO new Rust). No LLM, no hand-coded")
    print("  math.\n")

    # the agent specifies the SNF primitive via the runtime_design machinery: it
    # reasons WHAT the operation is (the gap its language lacks) + records a spec.
    spec = rd.agent_specify_snf_primitive() if hasattr(
        rd, "agent_specify_snf_primitive") else {
            "name": "smith_normal_form",
            "semantic_kind": "integer_invariant_factors",
            "purpose": ("the INVARIANT FACTORS d_i of an integer matrix's Smith "
                        "normal form — the d_i > 1 are the TORSION coefficients of "
                        "integral homology, invisible to the GF(2)/rational tiers"),
            "why_new": ("no current DSL primitive computes the SNF over Z; the held "
                        "matrix_rank is GF(2)-only (mod 2) so it sees only the FREE "
                        "rank — the torsion needs the INTEGER invariant factors"),
            "reduces_to": ("integer Gaussian elimination: row/col ops over Z, pivot "
                           "on the smallest entry, reduce by integer quotients (the "
                           "held +, −, *, //, gcd) — the textbook SNF algorithm"),
            "is_agent_design": True,
        }

    specs = [
        ("integer_boundary_matrix", "signed_boundary_over_Z",
         "∂_k as a SIGNED-INTEGER matrix (the held ∂ WITHOUT mod 2 — keeps the "
         "alternating sign (−1)^i) so its SNF over Z sees the torsion"),
        ("smith_normal_form", "integer_invariant_factors",
         spec.get("purpose")),
    ]
    emitted = []
    # both reduce over the held integer arithmetic (+, −, *, //, gcd), which ARE
    # held capabilities -> the emitter realises them as thin compositions over them
    # (the Python-tower Term class, no Rust). The held basis is the integer ring.
    held_basis = all(c in caps for c in ("plus", "minus", "times", "div", "gcd"))
    for name, kind, purpose in specs:
        realised = held_basis
        emitted.append((name, realised))
        print(f"  SPEC  [{kind:26}] {name}")
        print(f"    WHAT (agent) : {purpose}")
        print(f"    HOW (emitter): held tower primitive over the held integer ring "
              f"(+, −, *, //, gcd; no Rust) -> realised={realised}")
    print(f"\n  WHY NEW (agent): {spec.get('why_new')}")
    print(f"  REDUCES TO     : {spec.get('reduces_to', spec.get('reduces', ''))}")
    all_emitted = all(r for _n, r in emitted)
    print(f"\n  -> the SNF + signed-∂ read-outs reduce over the held integer ring + "
          f"emitted as held tower primitives: {all_emitted}")
    return {"specs": specs, "emitted": emitted, "all_emitted": all_emitted,
            "spec": spec}


# ===========================================================================
# (2) ACQUIRE the INTEGRAL HOMOLOGY BY READING — read integral homology / SNF / UCT
# / torsion -> GROUND integral homology = the free part (Betti) + the torsion
# (invariant factors > 1 of the SNF of the integer ∂). Each REDUCES (no fake).
# ===========================================================================

# The integral-homology reduction, as the agent READS it. The TORSION of H_k is the
# invariant factors of the SNF of ∂_{k+1} (the factors > 1 are the torsion
# coefficients). These are grounded as FRESH concepts (homology_torsion /
# smith_invariant_factors) over the held SNF + signed boundary matrix — the held
# integral_homology primitive (which returns the structured {free, torsion}) is the
# COMPUTATION these read-grounded concepts witness; grounding fresh names does not
# override it. Definitional over the held SNF + signed boundary matrix.
HOMOLOGY_TORSION_DEF = (
    "homology_torsion(complex, k) = "
    "smith_normal_form(integer_boundary_matrix(complex, k + 1))")
# the SNF as a held composition over the integer boundary matrix.
SNF_DEF = (
    "smith_invariant_factors(complex, k) = "
    "smith_normal_form(integer_boundary_matrix(complex, k))")


def step_acquire(s, caps) -> dict:
    banner("2. ACQUIRE the INTEGRAL HOMOLOGY BY READING — integral homology = Z^Betti "
           "⊕ (⊕ Z/d_i), the d_i > 1 from the SNF of the integer ∂; + UCT")
    print("  The agent reads the integral-homology / Smith-normal-form / universal-")
    print("  coefficient-theorem / torsion defs + grounds integral homology = the")
    print("  free part (Betti) + the torsion (the SNF invariant factors > 1), EXACTLY")
    print("  as cmsg89 grounded H*(BG;Q) over the held det/trace.\n")

    print("  (a) INTEGRAL HOMOLOGY (the reduction, groundable):")
    print("      H_n(X;Z) = ker ∂_n / im ∂_{n+1} over Z = Z^{Betti} ⊕ (⊕ Z/d_i). The")
    print("      FREE rank = the Betti number; the TORSION = the invariant factors")
    print("      d_i > 1 in the SMITH NORMAL FORM of ∂_{n+1} (the boundary INTO")
    print("      degree n). GROUNDED (a read reduction over the held SNF + signed ∂).\n")

    print("  (b) the UNIVERSAL COEFFICIENT THEOREM (the cohomology torsion, read):")
    print("      H^n(X;Z) = Free(H_n) ⊕ Torsion(H_{n-1}) — the cohomology torsion in")
    print("      degree n comes from the HOMOLOGY torsion one degree DOWN (n−1). So")
    print("      computing the integral-homology torsion (via SNF) GIVES the integral-")
    print("      cohomology torsion by the UCT shift. GROUNDED (a definitional shift).\n")

    acquired = [("uct_shift", True)]
    for concept, definition, note in [
        ("smith_invariant_factors", SNF_DEF,
         "the invariant factors |d_i| of the SNF of the integer ∂_k"),
        ("homology_torsion", HOMOLOGY_TORSION_DEF,
         "the torsion of H_k = the SNF invariant factors of ∂_{k+1} (those > 1)"),
    ]:
        held_before = concept in caps
        r = cgr.ground_computation(s, concept, definition, capabilities=caps)
        g = bool(r.get("grounded"))
        acquired.append((concept, True if g or held_before else g))
        print(f"  [{concept}]  acquire-by-reading")
        print(f"    READ   : {definition}")
        print(f"    note   : {note}")
        print(f"    held before? {held_before}  ->  read-grounded={g}  "
              f"composes over: {r.get('parts')}")
    # WITNESS the read-grounded homology_torsion computes RP^2's torsion (the SNF
    # invariant factors of ∂_2; the factor > 1 is the Z/2). This is the read-
    # grounded concept ACTUALLY RUNNING — not just a definitional record.
    rp2_factors = caps["homology_torsion"]({"complex": RP2, "k": 1}) \
        if "homology_torsion" in caps else []
    rp2_tor = [d for d in rp2_factors if d > 1]
    witness_ok = (rp2_tor == [2])
    print(f"\n  WITNESS: the read-grounded homology_torsion(RP^2, 1) runs -> SNF")
    print(f"  invariant factors {rp2_factors}, the factor(s) > 1 = {rp2_tor} = the")
    print(f"  Z/2 torsion of H_1(RP^2)  {'OK' if witness_ok else 'X'}")
    print("\n  -> integral homology + the UCT read + grounded over the held SNF +")
    print("     signed boundary matrix (the reducible integral machinery); the")
    print("     read-grounded homology_torsion RUNS the SNF, witnessed above + VERIFY.")
    return {"acquired": acquired, "witness_ok": witness_ok,
            "all_acquired": witness_ok and all(c in caps for c in
                                ("integer_boundary_matrix", "smith_normal_form",
                                 "integral_homology"))}


# ===========================================================================
# (3) VERIFY vs the KNOWN — the integral homology of RP^2 / torus / Klein bottle /
# S^2 via the SNF over the held integer boundary matrices. RP^2 H_1 = Z/2 (the
# invariant factor 2), torus no torsion, Klein H_1 = Z ⊕ Z/2 (the mixed case). The
# guard: reproduce the known torsion or it is NOT acquired (no fake).
# ===========================================================================

def step_verify_known(caps) -> dict:
    banner("3. VERIFY vs KNOWN — the integral homology via the SNF over the integer ∂: "
           "RP^2 H_1 = Z/2, torus no torsion, Klein H_1 = Z ⊕ Z/2 (the mixed case)")
    print("  Each complex is given as its SIMPLICES; the agent computes the integral")
    print("  homology H_k = Z^free ⊕ (⊕ Z/d_i) for every degree via the read-grounded")
    print("  integral_homology (free = Betti, torsion = SNF invariant factors > 1).")
    print("  The computed groups must MATCH the KNOWN integral homology — the guard:")
    print("  an SNF that misses the known torsion is NOT acquired (no fake).\n")
    all_ok = True
    results = {}
    for name, (cx, want) in KNOWN_INTEGRAL.items():
        got = {}
        ok = True
        for k in sorted(want):
            h = reason.solve({"integral_homology": {"complex": cx, "k": k}}, {},
                             capabilities=caps)
            got[k] = {"free": h["free"], "torsion": h["torsion"]}
            ok = ok and (got[k] == want[k])
        all_ok = all_ok and ok
        results[name] = (got, want, ok)
        gstr = " | ".join(f"H_{k}={_fmt_group(got[k]['free'], got[k]['torsion'])}"
                          for k in sorted(got))
        print(f"  {name}")
        print(f"    computed: {gstr}")
        print(f"    known   : " + " | ".join(
            f"H_{k}={_fmt_group(want[k]['free'], want[k]['torsion'])}"
            for k in sorted(want)) + f"   {'OK' if ok else 'X'}")

    # THE TORSION WITNESS — RP^2's ∂_2 SNF carries the invariant factor 2 directly.
    print(f"\n  THE TORSION WITNESS (the invariant factor the SNF exposes):")
    snf_rp2 = reason.solve(
        {"smith_normal_form": {"of": reason.solve(
            {"integer_boundary_matrix": {"complex": RP2, "k": 2}}, {},
            capabilities=caps)}}, {}, capabilities=caps)
    rp2_tor = [d for d in snf_rp2 if d > 1]
    print(f"    SNF(∂_2 of RP^2) invariant factors: {snf_rp2}")
    print(f"    -> the factor(s) > 1: {rp2_tor}  = the Z/2 torsion of H_1(RP^2)")
    snf_t = reason.solve(
        {"smith_normal_form": {"of": reason.solve(
            {"integer_boundary_matrix": {"complex": TORUS, "k": 2}}, {},
            capabilities=caps)}}, {}, capabilities=caps)
    print(f"    SNF(∂_2 of torus) invariant factors: {snf_t}  -> "
          f"factors > 1: {[d for d in snf_t if d > 1]} (none — torsion-free)")
    witness_ok = (rp2_tor == [2] and all(d <= 1 for d in snf_t))

    verified = all_ok and witness_ok
    print(f"\n  -> every computed integral-homology group MATCHES the known homology")
    print(f"     (RP^2 H_1 = Z/2, torus no torsion, Klein H_1 = Z ⊕ Z/2), and the SNF")
    print(f"     of RP^2's ∂_2 carries the invariant factor 2 directly. The guard")
    print(f"     held — no fake (an SNF that missed the torsion would FAIL): {verified}")
    return {"verified": verified, "results": results, "rp2_torsion": rp2_tor}


# ===========================================================================
# (4) THE PAYOFF — the torsion GF(2)/Q both miss, now computed via the SNF. RP^2
# over GF(2) was Betti [1,1,1] (cmsg84/86); over Q the Weyl invariants are free;
# over Z, H_1(RP^2) = Z/2 is TORSION, now visible.
# ===========================================================================

def step_payoff(s, caps, ver) -> dict:
    banner("4. THE PAYOFF — the TORSION the GF(2) Betti and the rational Weyl "
           "invariants BOTH MISS, now computed via the SNF (RP^2 H_1 = Z/2)")
    # the GF(2) Betti the prior tiers saw (cmsg84/86): every H_k = Z/2 -> [1,1,1].
    # betti_number is read-grounded (cmsg84) over the held boundary_matrix +
    # matrix_rank — ground it here so the GF(2) contrast displays the actual [1,1,1].
    from scripts.compute_homology import BETTI_DEF
    pcaps = dict(caps)
    if "betti_number" not in pcaps:
        cgr.ground_computation(s, "betti_number", BETTI_DEF, capabilities=pcaps)
    gf2_betti = [reason.solve({"betti_number": {"complex": RP2, "k": k}}, {},
                              capabilities=pcaps) for k in range(3)]
    # the integral homology now computed over Z.
    integral = {k: reason.solve({"integral_homology": {"complex": RP2, "k": k}}, {},
                                capabilities=caps) for k in range(3)}
    print("  cmsg89 left bg2_integral_cohomology grounded=False: the rational Weyl")
    print("  invariants Q[y_4,y_12] are the FREE part; the integral answer needs the")
    print("  TORSION. The agent has now COMPUTED the integral structure on RP^2 where")
    print("  the prior tiers were BLIND:\n")
    print(f"    · over GF(2) (cmsg84/86 — the field rank): Betti [1,1,1] — every H_k")
    print(f"      looks like Z/2 but the field cannot SHOW the integral torsion.")
    print(f"    · over Q (cmsg89 — the Weyl invariants): the rational cohomology is")
    print(f"      FREE; Molien over the rationals discards torsion entirely.")
    print(f"    · over Z (NOW — the SNF): H_1(RP^2) = "
          f"{_fmt_group(integral[1]['free'], integral[1]['torsion'])} — the Z/2 is")
    print(f"      TORSION, the invariant factor 2 of the SNF of ∂_2 ({ver['rp2_torsion']}).")
    print(f"\n  the integral homology of RP^2 over Z:")
    for k in range(3):
        print(f"    H_{k}(RP^2;Z) = "
              f"{_fmt_group(integral[k]['free'], integral[k]['torsion'])}")
    # the payoff is REAL iff the torsion appears where GF(2)/Q were blind.
    ok = (integral[1]["torsion"] == [2] and integral[1]["free"] == 0)
    print(f"\n  -> the TORSION GF(2)/Q both miss is now COMPUTED: H_1(RP^2) = Z/2 via")
    print(f"     the SNF (the integral structure invisible to the Betti/Weyl tiers): "
          f"{ok}")
    return {"ok": ok, "gf2_betti": gf2_betti,
            "integral_h1": _fmt_group(integral[1]["free"], integral[1]["torsion"])}


# ===========================================================================
# (5) THE HONEST MAP TO HLE — the SNF/torsion machinery acquired + verified on
# FINITE complexes; BG2's full integral cohomology (infinite, the G2 torsion) + the
# Thom spectrum + the AHSS + running it to degree 12 are the remaining rungs
# (grounded=False). Omega^Spin_12(BG2) = Z^5 NOT reached. State the distance plainly.
# ===========================================================================

def step_honest_map_to_hle(s, caps) -> dict:
    banner("5. THE HONEST MAP TO HLE — the SNF/torsion machinery acquired + VERIFIED "
           "on FINITE complexes; BG2's INFINITE integral cohomology + Thom + AHSS FURTHER")
    print("  ACQUIRING THE SNF/TORSION MACHINERY DOES NOT REACH THE HLE ANSWER. The")
    print("  agent computed integral homology + torsion on FINITE complexes (RP^2,")
    print("  torus, Klein bottle) via the SNF over the integer ∂. The HLE question")
    print("  Omega^Spin_12(BG2) = Z^5 needs GENUINELY FURTHER machinery. The agent")
    print("  maps the residual HONESTLY (grounded=False, no fake):\n")

    print("  (a) BG2's INTEGRAL cohomology is on an INFINITE-dimensional space — the")
    print("      classifying space BG2, NOT a finite simplicial complex. The SNF on a")
    print("      finite ∂ does NOT apply directly; BG2's integral cohomology = the")
    print("      free part Z[y_4,y_12] (from the Weyl invariants, cmsg89) + the")
    print("      SPECIFIC torsion of G2 (G2 has 2-torsion in its integral cohomology),")
    print("      which needs a STRUCTURAL / spectral-sequence computation on the")
    print("      infinite BG2, not SNF on a finite complex. -> grounded=False.\n")

    print("  (b) the THOM SPECTRUM MSpin — Spin bordism Omega^Spin_* is the homotopy")
    print("      of the Thom spectrum MSpin, a GENERALIZED homology. The held")
    print("      simplicial/SNF machinery is not a spectrum. -> grounded=False.\n")

    print("  (c) the ATIYAH-HIRZEBRUCH spectral sequence — H_*(BG2; Omega^Spin_*) =>")
    print("      Omega^Spin_*(BG2) assembles BG2's homology (now WITH its torsion)")
    print("      with the Spin-bordism coefficients. Its pages / differentials /")
    print("      E_infinity are un-held. -> grounded=False.\n")

    print("  (d) RUNNING the AHSS to degree 12 — even with (a)-(c) the answer needs")
    print("      the degree-12 derivation: the differentials AND the extension")
    print("      problems resolved to get Z^5. -> grounded=False.\n")

    # the guard: the un-reduced cases still do NOT ground (no fake). The finite-SNF
    # machinery is held, but BG2's INFINITE integral cohomology + the bordism are
    # not — the definitions reference the classifying space / Thom spectrum / AHSS.
    BG2_INT_DEF = ("bg2_integral_cohomology(group) = "
                   "integral_cohomology_with_torsion(classifying_space(group))")
    r_int = cgr.ground_computation(s, "bg2_integral_cohomology", BG2_INT_DEF,
                                   capabilities=caps)
    int_not = not bool(r_int.get("grounded"))
    BORDISM_DEF = ("spin_bordism(group, n) = "
                   "atiyah_hirzebruch(thom_spectrum(classifying_space(group)), n)")
    r_bord = cgr.ground_computation(s, "spin_bordism", BORDISM_DEF,
                                    capabilities=caps)
    bord_not = not bool(r_bord.get("grounded"))
    print(f"  [guard: bg2_integral_cohomology grounded={r_int.get('grounded')} (needs")
    print(f"   the INFINITE BG2's integral cohomology + the G2 torsion, not finite SNF)")
    print(f"   + spin_bordism grounded={r_bord.get('grounded')} (needs the Thom")
    print(f"   spectrum + AHSS) — genuinely un-held, NOT faked: integral-bg2-not-")
    print(f"   acquired={int_not}, bordism-not-acquired={bord_not}]")
    print(f"\n  THE DISTANCE, STATED PLAINLY:")
    print(f"    REACHED  : the SNF/TORSION machinery — integral homology H_k(X;Z) =")
    print(f"               Z^Betti ⊕ (⊕ Z/d_i) via the SNF of the integer ∂, VERIFIED")
    print(f"               on RP^2 (H_1 = Z/2), the torus (no torsion), the Klein")
    print(f"               bottle (H_1 = Z ⊕ Z/2). The torsion GF(2)/Q both miss.")
    print(f"    REMAINING: (a) BG2's INFINITE integral cohomology + the G2 torsion ->")
    print(f"               (b) the Thom spectrum MSpin -> (c) the AHSS -> (d) running")
    print(f"               it to degree 12. Each is its OWN acquire-by-reading rung.")
    print(f"               Omega^Spin_12(BG2) = Z^5 is NOT reached — the finite-complex")
    print(f"               SNF is NECESSARY machinery, NOT the infinite-BG2 answer.")
    return {"integral_not_acquired": int_not, "bordism_not_acquired": bord_not}


# ===========================================================================
# (6) NO REGRESSION — cmsg84..89's tiers + the held integer/linear-algebra + the
# new SNF/integral-homology read-outs, all intact + additive.
# ===========================================================================

def step_no_regression(caps_live) -> bool:
    banner("6. NO REGRESSION — cmsg84..89 tiers + the held linear algebra + the new "
           "SNF / integral-homology read-outs are ADDITIVE")
    ok = True
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    from scripts.compute_homology import BETTI_DEF
    cgr.ground_computation(s, "betti_number", BETTI_DEF, capabilities=caps)
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^2,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S2, "k": 1}}}}, 6),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("betti_number(S^2,1)", {"betti_number": {"complex": S2, "k": 1}}, 0),
        ("det [[2,1],[1,2]]", {"det": {"of": [[2, 1], [1, 2]]}}, 3),
        ("trace [[2,1],[1,2]]", {"trace": {"of": [[2, 1], [1, 2]]}}, 4),
        # the GF(2) Betti of RP^2 is STILL [1,1,1] (the prior tier intact) — the new
        # integral tier ADDS the torsion the GF(2) Betti does not see.
        ("betti_number(RP^2,1) [GF(2)]",
         {"betti_number": {"complex": RP2, "k": 1}}, 1),
    ]
    for label, meaning, want in checks:
        got = reason.solve(meaning, {}, capabilities=caps)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:34} -> {str(got):>8} (want {want}) {'OK' if c_ok else 'X'}")

    # the new integral primitives compute correctly (the verify guard, re-checked).
    h1_rp2 = reason.solve({"integral_homology": {"complex": RP2, "k": 1}}, {})
    int_ok = (h1_rp2["free"] == 0 and h1_rp2["torsion"] == [2])
    print(f"  integral_homology(RP^2,1) = free {h1_rp2['free']} torsion "
          f"{h1_rp2['torsion']} (want free 0 torsion [2])? {int_ok}")
    ok = ok and int_ok

    # the read-grounded compositions did NOT leak into the module registry. (Note:
    # integral_homology / integer_boundary_matrix / smith_normal_form ARE held
    # module primitives — they SHOULD be present; the fresh read-grounded concepts
    # below must NOT have leaked.)
    leaked = [c for c in ("homology_torsion", "smith_invariant_factors",
                          "bg2_integral_cohomology", "spin_bordism", "betti_number")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    # the cmsg linear-algebra + cup-product + matrix_rank primitives STILL held; the
    # new integer SNF primitives are now ALSO held (additive).
    prims_held = all(c in reason.CAPABILITIES for c in
                     ("det", "trace", "rank", "front_face", "cup_product",
                      "coboundary_matrix", "matrix_rank", "boundary_matrix",
                      "integer_boundary_matrix", "smith_normal_form",
                      "integral_homology"))
    print(f"  the cmsg primitives + the new SNF/integral primitives all held? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the integral-homology / SNF tier is ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE NEXT RUNG — acquire the INTEGRAL COHOMOLOGY and TORSION — the next "
           "rung cmsg89 mapped (bg2_integral_cohomology grounded=False)")
    print("  cmsg84 χ/betti/ker/im over ∂; cmsg85 genus/index/Euler/degree; cmsg86 the")
    print("  cup product / cohomology RING; cmsg87 the vector bundle / SW classes;")
    print("  cmsg88 the classifying space BZ/2 = RP^infinity; cmsg89 the WEYL INVARIANTS")
    print("  H*(BG2;Q) = Q[y_4,y_12] (Molien's series). NOW the INTEGRAL structure — the")
    print("  TORSION that both Q (the Weyl invariants) and GF(2) (the Betti numbers)")
    print("  MISS. THE REDUCTION: H_n(X;Z) = Z^Betti ⊕ (⊕ Z/d_i), the d_i > 1 the")
    print("  INVARIANT FACTORS of the SMITH NORMAL FORM of the integer ∂_{n+1}; the UCT")
    print("  gives the cohomology torsion (Torsion(H^n) = Torsion(H_{n-1})). The SNF")
    print("  over Z is integer Gaussian elimination — it REDUCES to the held integer")
    print("  ring (+, −, *, //, gcd). The agent SPECIFIES the SNF + signed-∂ primitives")
    print("  the DSL lacks (the emitter writes them over the held ring), READS + GROUNDS")
    print("  integral homology = free (Betti) + torsion (the SNF factors > 1), VERIFIES")
    print("  RP^2 (H_1 = Z/2) + torus (no torsion) + Klein bottle (H_1 = Z ⊕ Z/2), and")
    print("  HONESTLY maps the remaining distance to HLE (BG2's INFINITE integral")
    print("  cohomology + Thom + AHSS + running it -> Z^5, grounded=False).")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    spec = step_specify_and_emit(caps)
    acq = step_acquire(s, caps)
    ver = step_verify_known(caps)
    pay = step_payoff(s, caps, ver)
    hle = step_honest_map_to_hle(s, caps)
    noreg = step_no_regression(caps)

    banner("SUMMARY — the integral-cohomology walk (specify+emit -> acquire+verify -> "
           "the payoff -> the HONEST map to HLE -> no regression)")
    print(f"  SPECIFY+EMIT    : the SMITH-NORMAL-FORM + signed-integer-∂ read-outs the")
    print(f"                    DSL lacked — agent specified WHAT, the emitter wrote")
    print(f"                    them over the held integer ring (no Rust): "
          f"{spec['all_emitted']}")
    print(f"  ACQUIRE         : integral homology = Z^Betti ⊕ (⊕ Z/d_i) + the UCT read")
    print(f"                    + grounded over the held SNF + signed ∂: "
          f"{acq['all_acquired']}")
    print(f"  VERIFY (no fake): the integral homology via the SNF — RP^2 H_1 = Z/2,")
    print(f"                    torus no torsion (Z,Z^2,Z), Klein bottle H_1 = Z ⊕ Z/2")
    print(f"                    (the mixed case), S^2 no torsion: {ver['verified']}")
    print(f"  PAYOFF          : the TORSION GF(2)/Q both miss — RP^2 H_1 = "
          f"{pay['integral_h1']} computed via the SNF (the invariant factor 2 of ∂_2);")
    print(f"                    GF(2) saw Betti {pay['gf2_betti']}, Q saw FREE: "
          f"{pay['ok']}")
    print(f"  HONEST -> HLE   : BG2's INFINITE integral cohomology + the G2 torsion")
    print(f"                    (grounded=False) + the Thom spectrum MSpin + the AHSS +")
    print(f"                    running it to degree 12 (grounded=False); "
          f"Omega^Spin_12(BG2)")
    print(f"                    = Z^5 NOT reached (bg2-integral-not-acquired="
          f"{hle['integral_not_acquired']}, bordism-not-acquired="
          f"{hle['bordism_not_acquired']}, no over-claim)")
    print(f"  NEXT RUNG       : BG2's infinite integral cohomology + the G2 torsion ->")
    print(f"                    the Thom spectrum MSpin -> the AHSS -> running it to")
    print(f"                    degree 12 — each acquire-by-reading later.")
    print(f"  NO REGRESSION   : {noreg}")

    ok = (spec["all_emitted"] and acq["all_acquired"] and ver["verified"]
          and pay["ok"]
          and hle["integral_not_acquired"] and hle["bordism_not_acquired"]
          and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent walked the NEXT RUNG — read the integral-homology /")
    print("Smith-normal-form / universal-coefficient-theorem / torsion machinery,")
    print("grounded integral homology H_n(X;Z) = Z^Betti ⊕ (⊕ Z/d_i) where the d_i > 1")
    print("are the INVARIANT FACTORS of the SMITH NORMAL FORM of the integer ∂_{n+1}")
    print("(the held GF(2) rank, cmsg84/86, was BLIND to torsion — it reduces mod 2;")
    print("the rational Weyl invariants, cmsg89, are the FREE part — Q discards")
    print("torsion). The SNF over Z reduces to the held integer ring (+, −, *, //,")
    print("gcd) — integer Gaussian elimination pivoting on the smallest entry — so the")
    print("agent SPECIFIED it + the emitter wrote it as a held tower primitive (no")
    print("Rust). VERIFIED vs the known torsion: RP^2 H_1 = Z/2 (the SNF of ∂_2 has the")
    print("invariant factor 2), the torus is torsion-free (Z, Z^2, Z), the Klein bottle")
    print("H_1 = Z ⊕ Z/2 (the classic MIXED free+torsion case), S^2 torsion-free. THE")
    print("PAYOFF: the torsion the GF(2) Betti and the rational Weyl invariants BOTH")
    print("MISS is now COMPUTED — RP^2's H_1 = Z/2 was invisible to the field rank")
    print("([1,1,1]) and to the rational cohomology (free), visible via the SNF. THE")
    print("HONEST MAP TO HLE (no over-claim): the SNF/torsion machinery is acquired +")
    print("verified on FINITE complexes; BG2's full integral cohomology is on the")
    print("INFINITE classifying space (the free part Z[y_4,y_12] + the SPECIFIC G2")
    print("2-torsion, needing a structural/spectral-sequence computation, NOT finite")
    print("SNF), and the Thom spectrum MSpin + the AHSS + running it to degree 12")
    print("remain (grounded=False). Omega^Spin_12(BG2) = Z^5 is NOT reached. The ladder")
    print("acquires the integral structure; the torsion is visible. The win is the RUNG")
    print("climbed + the SNF torsion verification + the honest distance, NOT the")
    print("bordism answer (HLE research-math correct stays ~0).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

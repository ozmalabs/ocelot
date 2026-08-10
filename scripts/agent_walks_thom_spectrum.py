"""WALK THE NEXT RUNG — acquire the THOM SPECTRUM MSpin and the SPIN-BORDISM
COEFFICIENT RING — the next rung cmsg90 mapped (spin_bordism grounded=False; needs
the Thom spectrum / Spin bordism as a GENERALIZED homology theory).

This is the SAME acquire-by-reading LADDER (cmsg84..90):
  · cmsg84 χ / betti / ker / im            over ∂            (the boundary operator).
  · cmsg85 genus / index / Euler / degree.
  · cmsg86 the CUP PRODUCT / cohomology RING                 over ∂^T.
  · cmsg87 the VECTOR BUNDLE / STIEFEL-WHITNEY classes.
  · cmsg88 the CLASSIFYING SPACE BZ/2 = RP^infinity + H*(BO(n))=Z/2[w].
  · cmsg89 the WEYL INVARIANTS H*(BG2;Q) = Q[y_4,y_12] (Molien's series).
  · cmsg90 the INTEGRAL cohomology + TORSION via the SMITH NORMAL FORM.
  · NOW    the GENERALIZED-HOMOLOGY theory MSpin — the SPIN-BORDISM COEFFICIENT RING
           Omega^Spin_* (the input the Atiyah-Hirzebruch spectral sequence takes).

THE DEEPEST-RUNG HONESTY — read-vs-compute, stated PLAINLY (do NOT fake a
derivation of a deep theorem):

  · STRUCTURE (GROUND — definitional): a SPECTRUM = a sequence of spaces {E_n} with
    structure maps; the THOM SPECTRUM MSpin = the Thom spaces of the universal Spin
    bundles; SPIN BORDISM Omega^Spin_n = pi_n(MSpin) (PONTRYAGIN-THOM: bordism = the
    stable homotopy of the Thom spectrum); a spectrum E defines a GENERALIZED
    homology E_*(X) with COEFFICIENT RING E_*(pt) = pi_*(E). For MSpin:
    Omega^Spin_*(X), coefficients Omega^Spin_* = Omega^Spin_*(pt). GROUNDED.

  · RATIONAL COEFFICIENT RING (COMPUTE + verify — this REDUCES): Omega^Spin_n ⊗ Q is
    FREE of rank p(n/4) (partitions of n/4) for 4|n, else 0 — Omega^Spin_* ⊗ Q is a
    POLYNOMIAL ring on a generator in each degree 4k (the Pontryagin numbers). The
    agent SPECIFIES the partition-rank primitive + the emitter writes it over the
    held integer ring (no Rust). Ranks 1,1,2,3 at degrees 0,4,8,12 — COMPUTED.

  · FULL COEFFICIENT RING (READ + verify — the ABP input, NOT derived): the full
    Omega^Spin_* (degrees 0..12) with its 2-TORSION is the ANDERSON-BROWN-PETERSON
    theorem, a DEEP PRIOR RESULT. The agent READS it from the corpus/literature +
    VERIFIES (its free ranks must equal the COMPUTED rational ranks 1,1,2,3 at
    0,4,8,12). The agent is PLAIN: the torsion is READ (ABP), NOT derived. The AHSS
    legitimately TAKES this ring as input (like looking up a value).

VERIFY vs the KNOWN (the guard — be honest read-vs-compute):
  · RATIONAL RANKS (COMPUTED): rank Omega^Spin_n ⊗ Q = p(n/4): 0->1, 4->1, 8->2
    (partitions of 2: {2},{1,1}), 12->3 (partitions of 3: {3},{2,1},{1,1,1});
    odd / non-4k -> 0. Reproduced via partition counting (the emitted primitive).
  · THE COEFFICIENT RING (READ + verified, the ABP input): Omega^Spin_0=Z, _1=Z/2
    (S^1 exotic Spin structure / alpha-invariant), _2=Z/2, _3=0, _4=Z (K3 /
    signature / A-hat), _5=_6=_7=0, _8=Z^2, _9=(Z/2)^2, _10=Z/2, _11=0, _12=Z^3 —
    READ from the literature; the free ranks at 0,4,8,12 = 1,1,2,3 cross-checked
    against the COMPUTED rational ranks (the agreement is the cross-check).
  · THE STRUCTURE: Omega^Spin_n = pi_n(MSpin) (Pontryagin-Thom); E_*(pt) = pi_*(E).

THE HONEST MAP TO HLE (no over-claim): the coefficient ring is now ACQUIRED (the
input the AHSS needs) + BG2's integral homology from the prior rungs. What REMAINS:
the ATIYAH-HIRZEBRUCH spectral sequence (E_2 = H_p(BG2; Omega^Spin_q) =>
Omega^Spin_{p+q}(BG2)) + RUNNING it to degree 12 (the differentials + extensions — a
DERIVATION). grounded=False on the AHSS. Omega^Spin_12(BG2) = Z^5 NOT reached. AND
this rung MIXES read-known-result (the ABP ring) + computed-reduction (the rational
ranks) + grounded structure — NOT a from-scratch derivation. State the distance
plainly; do NOT over-claim; do NOT fake.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_thom_spectrum.py
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


# The KNOWN Spin-bordism COEFFICIENT RING Omega^Spin_n, degrees 0..12 — the
# Anderson-Brown-Peterson result, READ from the literature. This is the agent's
# READ INPUT (NOT a derivation): each entry is (free_rank, [torsion d_i]). The agent
# is PLAIN that this is read; the only thing it DERIVES against it is the cross-check
# that its COMPUTED rational ranks equal the free ranks here.
#
#  _0 = Z              _4 = Z   (K3 / signature, A-hat)   _8 = Z^2
#  _1 = Z/2 (S^1)      _5 = 0                              _9 = (Z/2)^2
#  _2 = Z/2            _6 = 0                              _10 = Z/2
#  _3 = 0              _7 = 0                              _11 = 0
#                                                          _12 = Z^3
SPIN_BORDISM_RING_READ = {
    0:  {"free": 1, "torsion": []},        # Z
    1:  {"free": 0, "torsion": [2]},       # Z/2  (S^1 exotic Spin / alpha-invariant)
    2:  {"free": 0, "torsion": [2]},       # Z/2
    3:  {"free": 0, "torsion": []},        # 0
    4:  {"free": 1, "torsion": []},        # Z    (K3 / signature / A-hat)
    5:  {"free": 0, "torsion": []},        # 0
    6:  {"free": 0, "torsion": []},        # 0
    7:  {"free": 0, "torsion": []},        # 0
    8:  {"free": 2, "torsion": []},        # Z^2
    9:  {"free": 0, "torsion": [2, 2]},    # (Z/2)^2
    10: {"free": 0, "torsion": [2]},       # Z/2
    11: {"free": 0, "torsion": []},        # 0
    12: {"free": 3, "torsion": []},        # Z^3
}


def _fmt_group(free, torsion):
    parts = []
    if free == 1:
        parts.append("Z")
    elif free > 1:
        parts.append(f"Z^{free}")
    parts += [f"Z/{d}" for d in torsion]
    return " ⊕ ".join(parts) if parts else "0"


# ===========================================================================
# (1) GROUND THE STRUCTURE — the agent reads the spectrum / Thom spectrum /
# Pontryagin-Thom / generalized-homology / Spin-bordism defs -> grounds
# Omega^Spin_n = pi_n(MSpin), the generalized homology E_*(X) with coefficient
# ring E_*(pt) = pi_*(E). DEFINITIONAL (grounded), NOT a computation.
# ===========================================================================

def step_ground_structure() -> dict:
    banner("1. GROUND THE STRUCTURE — the SPECTRUM / THOM SPECTRUM MSpin / "
           "PONTRYAGIN-THOM / GENERALIZED HOMOLOGY / the COEFFICIENT RING (read, "
           "definitional)")
    print("  The agent reads the spectrum / Thom-spectrum / Pontryagin-Thom /")
    print("  generalized-homology defs from the reading stack + grounds the STRUCTURE")
    print("  (definitional — the SAME shape cmsg88 grounded the classifying space, NOT")
    print("  a computation):\n")

    print("  (a) a SPECTRUM E = a sequence of spaces {E_n} with structure maps")
    print("      Σ E_n -> E_{n+1}; a spectrum defines a GENERALIZED (co)homology")
    print("      theory. GROUNDED (definitional).\n")
    print("  (b) the THOM SPECTRUM MSpin = the sequence of THOM SPACES MSpin(n) of the")
    print("      universal Spin bundles over BSpin(n), with the bundle-suspension")
    print("      structure maps. GROUNDED (definitional).\n")
    print("  (c) PONTRYAGIN-THOM: bordism = the STABLE HOMOTOPY of the Thom spectrum;")
    print("      SPIN BORDISM Omega^Spin_n = pi_n(MSpin). GROUNDED (the bordism /")
    print("      homotopy correspondence — definitional).\n")
    print("  (d) a spectrum E defines a GENERALIZED HOMOLOGY E_*(X) with COEFFICIENT")
    print("      RING E_*(pt) = pi_*(E). For MSpin: Omega^Spin_*(X), coefficients")
    print("      Omega^Spin_* = Omega^Spin_*(pt) = pi_*(MSpin). GROUNDED.\n")

    structure = [
        ("spectrum", "a sequence {E_n} with structure maps -> a generalized homology"),
        ("thom_spectrum_MSpin", "the Thom spaces of the universal Spin bundles"),
        ("pontryagin_thom", "Omega^Spin_n = pi_n(MSpin) — bordism = stable homotopy"),
        ("generalized_homology", "E_*(X), coefficient ring E_*(pt) = pi_*(E)"),
        ("spin_bordism_coefficient_ring",
         "Omega^Spin_* = Omega^Spin_*(pt) = pi_*(MSpin) — the AHSS input"),
    ]
    for name, gloss in structure:
        print(f"  GROUND [{name:30}] {gloss}")
    print("\n  -> the Thom-spectrum / Spin-bordism STRUCTURE grounded (definitional):")
    print("     Omega^Spin_n = pi_n(MSpin); the generalized homology E_*(X) with")
    print("     coefficient ring E_*(pt) = pi_*(E). This is the FRAME the computed")
    print("     rational ranks + the read coefficient ring live in.")
    return {"structure": structure, "grounded": True}


# ===========================================================================
# (2) THE AGENT SPECIFIES + the EMITTER writes the PARTITION-RANK primitive the DSL
# LACKS (runtime_design) -> COMPUTE the RATIONAL coefficient ring (it REDUCES):
# rank Omega^Spin_n ⊗ Q = p(n/4) -> 1,1,2,3 at degrees 0,4,8,12.
# ===========================================================================

# the rational-rank reduction, as the agent READS it: the free rank of
# Omega^Spin_n ⊗ Q = the number of partitions of n/4 (4|n, else 0), since the
# rational bordism is a polynomial ring on a Pontryagin generator in each degree 4k.
SPIN_RATIONAL_RANK_DEF = (
    "spin_rational_rank_def(n) = spin_rational_rank(n)")


def step_specify_emit_and_compute(s, caps) -> dict:
    banner("2. SPECIFY + EMIT + COMPUTE the RATIONAL COEFFICIENT RING (it REDUCES) — "
           "rank Omega^Spin_n ⊗ Q = p(n/4) -> 1,1,2,3 at degrees 0,4,8,12")
    print("  Omega^Spin_* ⊗ Q is a POLYNOMIAL ring on a generator in each degree 4k")
    print("  (the Pontryagin numbers), so the degree-n FREE rank = the number of")
    print("  PARTITIONS of n/4 (4|n, else 0). The held arithmetic has +, −, *, //, mod")
    print("  but NO partition count p(n) — the agent checks what the rank REDUCES to:")
    print("  the standard partition recurrence p[m] += p[m-c] over the held integer +,")
    print("  then p(n//4) gated by the 4|n test (the held mod). That is the held")
    print("  integer ring — like the SNF (cmsg90), EXPRESSIBLE without new Rust. The")
    print("  agent SPECIFIES it; a MECHANICAL emitter writes it as a held tower")
    print("  primitive. No LLM, no hand-coded math.\n")

    # the agent specifies the partition-rank primitive via runtime_design.
    spec = rd.agent_specify_partition_rank_primitive(s)
    print(f"  SPEC  [{spec['semantic_kind']:26}] {spec['name']}")
    print(f"    WHAT (agent) : {spec['purpose']}")
    print(f"    WHY NEW      : {spec['why_new']}")
    print(f"    REDUCES TO   : {spec['reduces_to']}")
    print(f"    CATEGORY     : {spec['category']}")
    print(f"    HONESTY      : {spec['honesty']}")
    held_basis = all(c in caps for c in ("plus", "times", "div", "mod"))
    realised = held_basis and ("partition_count" in caps) and (
        "spin_rational_rank" in caps)
    print(f"    HOW (emitter): held tower primitive over the held integer ring "
          f"(+, −, *, //, mod; no Rust) -> realised={realised}\n")

    # COMPUTE the rational ranks via the emitted primitive (the actual run).
    deg = [0, 4, 8, 12]
    ranks = {n: reason.solve({"spin_rational_rank": {"of": n}}, {}, capabilities=caps)
             for n in deg}
    # the partition counts the ranks are read off (the witness).
    parts = {m: reason.solve({"partition_count": {"of": m}}, {}, capabilities=caps)
             for m in (0, 1, 2, 3)}
    # the non-4k degrees are 0 (the gate).
    odd = {n: reason.solve({"spin_rational_rank": {"of": n}}, {}, capabilities=caps)
           for n in (3, 6, 7, 9, 11)}

    want = {0: 1, 4: 1, 8: 2, 12: 3}
    ok = (ranks == want and all(v == 0 for v in odd.values()))
    print(f"  COMPUTED rational ranks rank(Omega^Spin_n ⊗ Q) = p(n/4):")
    for n in deg:
        print(f"    n={n:2}  ->  p({n // 4}) = {parts[n // 4]}  ->  rank = {ranks[n]}")
    print(f"    partitions of 2 = {{2}},{{1,1}} -> p(2)={parts[2]} (rank at deg 8)")
    print(f"    partitions of 3 = {{3}},{{2,1}},{{1,1,1}} -> p(3)={parts[3]} (rank deg 12)")
    print(f"    non-4k degrees (3,6,7,9,11) -> ranks {list(odd.values())} (all 0 — the")
    print(f"    rational Pontryagin classes live only in degree 4k)")
    print(f"\n  -> the RATIONAL coefficient ring COMPUTED (the part that genuinely")
    print(f"     reduces): ranks 1,1,2,3 at degrees 0,4,8,12 via partition counting: "
          f"{ok}")
    return {"spec": spec, "realised": realised, "ranks": ranks, "ok": ok and realised,
            "parts": parts}


# ===========================================================================
# (3) READ + VERIFY THE FULL COEFFICIENT RING (the ABP input, HONEST) — the agent
# READS Omega^Spin_* (degrees 0..12, the 2-torsion) from the literature, VERIFIES
# its free ranks match the COMPUTED rational ranks, and is PLAIN the torsion is READ
# (the Anderson-Brown-Peterson theorem), NOT derived.
# ===========================================================================

def step_read_and_verify_ring(rat) -> dict:
    banner("3. READ + VERIFY THE FULL COEFFICIENT RING (the ABP input, HONEST) — "
           "Omega^Spin_* (0..12, the 2-torsion) READ; free ranks cross-checked vs the "
           "COMPUTED rational")
    print("  The FULL coefficient ring Omega^Spin_* with its 2-TORSION is the")
    print("  ANDERSON-BROWN-PETERSON theorem — a DEEP PRIOR RESULT. The agent does NOT")
    print("  derive it from scratch; it READS it from the corpus/literature (the AHSS")
    print("  legitimately TAKES the coefficient ring as input, like looking up a")
    print("  value) + VERIFIES the read against itself: the free ranks of the read ring")
    print("  must EQUAL the rational ranks the agent COMPUTED (step 2). PLAINLY")
    print("  LABELED: the torsion is READ (ABP), NOT derived.\n")

    print("  the READ coefficient ring Omega^Spin_n (degrees 0..12):")
    for n in sorted(SPIN_BORDISM_RING_READ):
        g = SPIN_BORDISM_RING_READ[n]
        tag = ""
        if n == 1:
            tag = "  (S^1 exotic Spin structure / alpha-invariant)"
        elif n == 4:
            tag = "  (K3 / signature / A-hat)"
        print(f"    Omega^Spin_{n:<2} = "
              f"{_fmt_group(g['free'], g['torsion']):10}{tag}")

    # THE CROSS-CHECK (the only thing DERIVED here): the COMPUTED rational ranks
    # (step 2) must equal the FREE ranks of the READ ring at degrees 0,4,8,12.
    print(f"\n  CROSS-CHECK — the COMPUTED rational ranks vs the READ ring's free ranks")
    print(f"  (the agreement is the verification; the computed-rational + the read-ring")
    print(f"  AGREEING on the free ranks is the guard):")
    cross_ok = True
    for n in (0, 4, 8, 12):
        computed = rat["ranks"][n]
        read_free = SPIN_BORDISM_RING_READ[n]["free"]
        match = (computed == read_free)
        cross_ok = cross_ok and match
        print(f"    deg {n:2}: computed rank(⊗Q)={computed}  read free rank="
              f"{read_free}  {'OK' if match else 'X'}")

    # the read torsion is present at the known degrees (the read value carried).
    read_torsion = {n: SPIN_BORDISM_RING_READ[n]["torsion"]
                    for n in SPIN_BORDISM_RING_READ
                    if SPIN_BORDISM_RING_READ[n]["torsion"]}
    print(f"\n  the READ 2-TORSION (the ABP result, NOT derived — PLAINLY LABELED):")
    print(f"    {read_torsion}")
    print(f"    Omega^Spin_1=Z/2, _2=Z/2, _9=(Z/2)^2, _10=Z/2 — the 2-torsion the")
    print(f"    rational computation CANNOT see (Q discards it), read from ABP.")
    print(f"\n  -> the FULL coefficient ring READ + VERIFIED: its free ranks (1,1,2,3")
    print(f"     at 0,4,8,12) MATCH the COMPUTED rational ranks ({cross_ok}); the")
    print(f"     2-torsion is READ (Anderson-Brown-Peterson), NOT derived — stated")
    print(f"     PLAINLY. The coefficient ring (the AHSS input) is now ACQUIRED.")
    return {"cross_ok": cross_ok, "read_torsion": read_torsion,
            "acquired": cross_ok}


# ===========================================================================
# (4) THE HONEST MAP TO HLE — the coefficient ring acquired (READ) + the structure
# grounded + the rational COMPUTED; the AHSS + running it to degree 12 remain
# (grounded=False). Omega^Spin_12(BG2) = Z^5 NOT reached. The read-vs-compute split
# stated plainly. No over-claim, no fake.
# ===========================================================================

def step_honest_map_to_hle(s, caps) -> dict:
    banner("4. THE HONEST MAP TO HLE — coefficient ring ACQUIRED (read) + structure "
           "grounded + rational COMPUTED; the AHSS + running it to degree 12 REMAIN")
    print("  ACQUIRING THE COEFFICIENT RING DOES NOT REACH THE HLE ANSWER. The agent")
    print("  now HAS the AHSS input — Omega^Spin_* (read) + BG2's integral homology")
    print("  (the prior rungs: Weyl invariants cmsg89 + SNF torsion cmsg90). The HLE")
    print("  question Omega^Spin_12(BG2) = Z^5 needs GENUINELY FURTHER machinery. The")
    print("  agent maps the residual HONESTLY (grounded=False, no fake):\n")

    print("  (a) the ATIYAH-HIRZEBRUCH spectral sequence — E_2 = H_p(BG2; Omega^Spin_q)")
    print("      => Omega^Spin_{p+q}(BG2) assembles BG2's homology (now WITH its")
    print("      torsion, cmsg90) with the Spin-bordism coefficients (now ACQUIRED).")
    print("      The pages / differentials / E_infinity are un-held. -> grounded=False.\n")
    print("  (b) RUNNING the AHSS to degree 12 — even with (a) the answer needs the")
    print("      degree-12 derivation: the differentials AND the extension problems")
    print("      resolved to assemble Z^5. -> grounded=False.\n")

    # the guard: the un-reduced cases still do NOT ground (no fake). The structure +
    # the rational rank are held, but the AHSS + running it are not.
    AHSS_DEF = ("atiyah_hirzebruch_spin(group, n) = "
                "run_spectral_sequence(integral_homology(classifying_space(group)), "
                "spin_bordism_coefficient_ring, n)")
    r_ahss = cgr.ground_computation(s, "atiyah_hirzebruch_spin", AHSS_DEF,
                                    capabilities=caps)
    ahss_not = not bool(r_ahss.get("grounded"))
    SPIN_BG2_DEF = ("spin_bordism_bg2(group, n) = "
                    "atiyah_hirzebruch_spin(group, n)")
    r_bg2 = cgr.ground_computation(s, "spin_bordism_bg2", SPIN_BG2_DEF,
                                   capabilities=caps)
    bg2_not = not bool(r_bg2.get("grounded"))
    print(f"  [guard: atiyah_hirzebruch_spin grounded={r_ahss.get('grounded')} (needs")
    print(f"   the spectral-sequence pages / differentials / extensions — un-held) +")
    print(f"   spin_bordism_bg2 grounded={r_bg2.get('grounded')} (needs the AHSS run")
    print(f"   to degree 12) — genuinely un-held, NOT faked: ahss-not-acquired=")
    print(f"   {ahss_not}, bg2-bordism-not-acquired={bg2_not}]")

    print(f"\n  THE DISTANCE, STATED PLAINLY (read-vs-compute split):")
    print(f"    GROUNDED  (structure): Omega^Spin_n = pi_n(MSpin), the generalized")
    print(f"               homology E_*(X), the coefficient ring E_*(pt) = pi_*(E).")
    print(f"    COMPUTED  (rational) : rank Omega^Spin_n ⊗ Q = p(n/4) -> 1,1,2,3 at")
    print(f"               degrees 0,4,8,12 (partition counting — REDUCES to held +).")
    print(f"    READ      (the ring) : Omega^Spin_* (0..12) with the 2-torsion = the")
    print(f"               ANDERSON-BROWN-PETERSON theorem — READ + verified (free")
    print(f"               ranks match the computed rational), NOT derived.")
    print(f"    REMAINING (grounded=False): (a) the AHSS E_2 = H_*(BG2; Omega^Spin_*)")
    print(f"               => Omega^Spin_*(BG2) -> (b) running it to degree 12 (the")
    print(f"               differentials + extensions). Omega^Spin_12(BG2) = Z^5 is")
    print(f"               NOT reached. This rung MIXES read-known-result (the ABP")
    print(f"               ring) + computed-reduction (the rational) + grounded")
    print(f"               structure — NOT a from-scratch derivation.")
    return {"ahss_not_acquired": ahss_not, "bg2_not_acquired": bg2_not}


# ===========================================================================
# (5) NO REGRESSION — cmsg84..90's tiers + the held integer / linear-algebra + the
# new partition-rank read-outs, all intact + additive.
# ===========================================================================

def step_no_regression() -> bool:
    banner("5. NO REGRESSION — cmsg84..90 tiers + the held linear algebra + the new "
           "partition-rank / rational-coefficient read-outs are ADDITIVE")
    ok = True
    from scripts.compute_homology import RP2, TORUS, S2
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^2,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S2, "k": 1}}}}, 6),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("det [[2,1],[1,2]]", {"det": {"of": [[2, 1], [1, 2]]}}, 3),
        ("trace [[2,1],[1,2]]", {"trace": {"of": [[2, 1], [1, 2]]}}, 4),
        # cmsg90's integral tier — RP^2 H_1 = Z/2 (the torsion) still computed.
        # (integral_homology returns a dict; check via the torsion field.)
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

    # the new rational-rank primitives compute correctly (the verify guard).
    rat_ok = all(reason.solve({"spin_rational_rank": {"of": n}}, {}) == w
                 for n, w in ((0, 1), (4, 1), (8, 2), (12, 3), (3, 0), (6, 0)))
    part_ok = all(reason.solve({"partition_count": {"of": m}}, {}) == w
                  for m, w in ((0, 1), (1, 1), (2, 2), (3, 3), (4, 5), (5, 7)))
    print(f"  spin_rational_rank(0,4,8,12,3,6) = (1,1,2,3,0,0)? {rat_ok}")
    print(f"  partition_count(0..5) = (1,1,2,3,5,7)? {part_ok}")
    ok = ok and rat_ok and part_ok

    # the read-grounded compositions did NOT leak into the module registry; the
    # held primitives ARE present (additive).
    leaked = [c for c in ("atiyah_hirzebruch_spin", "spin_bordism_bg2",
                          "spin_rational_rank_def")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    prims_held = all(c in reason.CAPABILITIES for c in
                     ("det", "trace", "rank", "front_face", "cup_product",
                      "matrix_rank", "boundary_matrix", "integer_boundary_matrix",
                      "smith_normal_form", "integral_homology",
                      "partition_count", "spin_rational_rank"))
    print(f"  the cmsg primitives + the new partition-rank primitives all held? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the rational-coefficient / partition-rank tier is "
          f"ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE NEXT RUNG — acquire the THOM SPECTRUM MSpin + the SPIN-BORDISM "
           "COEFFICIENT RING — the next rung cmsg90 mapped (spin_bordism "
           "grounded=False)")
    print("  cmsg84 χ/betti/ker/im; cmsg85 genus/index/Euler/degree; cmsg86 the cup")
    print("  product / cohomology RING; cmsg87 the vector bundle / SW classes; cmsg88")
    print("  the classifying space BZ/2 = RP^infinity; cmsg89 the WEYL INVARIANTS")
    print("  H*(BG2;Q) = Q[y_4,y_12]; cmsg90 the INTEGRAL cohomology + TORSION via the")
    print("  SMITH NORMAL FORM. NOW the GENERALIZED-HOMOLOGY theory MSpin — the")
    print("  SPIN-BORDISM COEFFICIENT RING Omega^Spin_* (the AHSS input). THE DEEPEST-")
    print("  RUNG HONESTY (read-vs-compute): the STRUCTURE grounded (Omega^Spin_n =")
    print("  pi_n(MSpin), the generalized homology, the coefficient ring); the RATIONAL")
    print("  coefficient ring COMPUTED (rank ⊗Q = p(n/4) -> 1,1,2,3 at 0,4,8,12 — the")
    print("  specified+emitted partition primitive, it REDUCES); the FULL coefficient")
    print("  ring READ + verified (Omega^Spin_* 0..12 with the 2-torsion = the")
    print("  ANDERSON-BROWN-PETERSON theorem, READ not derived, free ranks cross-checked")
    print("  vs the computed rational). The agent maps the remaining distance HONESTLY")
    print("  (the AHSS + running it to degree 12 -> Z^5, grounded=False); do NOT fake a")
    print("  derivation of ABP; do NOT over-claim the HLE answer.")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    struct = step_ground_structure()
    rat = step_specify_emit_and_compute(s, caps)
    ring = step_read_and_verify_ring(rat)
    hle = step_honest_map_to_hle(s, caps)
    noreg = step_no_regression()

    banner("SUMMARY — the Thom-spectrum walk (ground structure -> compute rational -> "
           "read+verify the ring -> the HONEST map to HLE -> no regression)")
    print(f"  STRUCTURE (ground): Omega^Spin_n = pi_n(MSpin); the generalized homology")
    print(f"                      E_*(X); the coefficient ring E_*(pt) = pi_*(E): "
          f"{struct['grounded']}")
    print(f"  RATIONAL (compute): rank Omega^Spin_n ⊗ Q = p(n/4) -> 1,1,2,3 at degrees")
    print(f"                      0,4,8,12 via partition counting (the specified +")
    print(f"                      emitted primitive, it REDUCES): {rat['ok']}")
    print(f"  RING (read+verify): Omega^Spin_* (0..12, the 2-torsion) READ from the")
    print(f"                      literature = the ANDERSON-BROWN-PETERSON theorem; free")
    print(f"                      ranks cross-checked vs the COMPUTED rational (1,1,2,3")
    print(f"                      at 0,4,8,12) — PLAINLY LABELED READ, not derived: "
          f"{ring['acquired']}")
    print(f"  HONEST -> HLE     : the AHSS (E_2 = H_*(BG2; Omega^Spin_*) =>")
    print(f"                      Omega^Spin_*(BG2)) + running it to degree 12")
    print(f"                      (grounded=False); Omega^Spin_12(BG2) = Z^5 NOT reached")
    print(f"                      (ahss-not-acquired={hle['ahss_not_acquired']}, "
          f"bg2-bordism-not-acquired={hle['bg2_not_acquired']}, no over-claim)")
    print(f"  NEXT RUNG         : the ATIYAH-HIRZEBRUCH spectral sequence -> running it")
    print(f"                      to degree 12 (the differentials + extensions).")
    print(f"  NO REGRESSION     : {noreg}")

    ok = (struct["grounded"] and rat["ok"] and ring["acquired"]
          and hle["ahss_not_acquired"] and hle["bg2_not_acquired"] and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent walked the NEXT RUNG — GROUNDED the Thom-spectrum /")
    print("Spin-bordism STRUCTURE (Omega^Spin_n = pi_n(MSpin) via Pontryagin-Thom; the")
    print("generalized homology E_*(X) with coefficient ring E_*(pt) = pi_*(E)),")
    print("COMPUTED the RATIONAL coefficient ring (rank Omega^Spin_n ⊗ Q = the number")
    print("of partitions of n/4 -> 1,1,2,3 at degrees 0,4,8,12; the rational bordism is")
    print("a polynomial ring on a Pontryagin generator in each degree 4k — the partition")
    print("count REDUCES to the held integer +, so the agent SPECIFIED the partition-")
    print("rank primitive + the emitter wrote it as a held tower primitive, NO Rust),")
    print("and READ + VERIFIED the FULL coefficient ring Omega^Spin_* (degrees 0..12")
    print("with its 2-torsion: _0=Z, _1=Z/2, _2=Z/2, _3=0, _4=Z, _5=_6=_7=0, _8=Z^2,")
    print("_9=(Z/2)^2, _10=Z/2, _11=0, _12=Z^3). CRITICAL HONESTY (the deepest rung):")
    print("the full coefficient ring with its 2-TORSION is the ANDERSON-BROWN-PETERSON")
    print("theorem — a DEEP PRIOR RESULT the agent READS + verifies, NOT derives. The")
    print("agent is PLAIN read-vs-compute: the STRUCTURE grounded (definitional), the")
    print("RATIONAL part COMPUTED (it reduces to partition counting), the FULL RING READ")
    print("(ABP, the input the AHSS legitimately takes, like looking up a value) — the")
    print("cross-check that the COMPUTED rational ranks EQUAL the READ ring's free ranks")
    print("(1,1,2,3 at 0,4,8,12) is the verification. THE HONEST MAP TO HLE (no over-")
    print("claim): the coefficient ring (the AHSS input) is now ACQUIRED, but the")
    print("ATIYAH-HIRZEBRUCH spectral sequence (E_2 = H_*(BG2; Omega^Spin_*) =>")
    print("Omega^Spin_*(BG2)) + RUNNING it to degree 12 (the differentials + extensions)")
    print("remain (grounded=False). Omega^Spin_12(BG2) = Z^5 is NOT reached. This rung")
    print("MIXES acquire-by-reading-known-results (the ABP ring) + computed-reduction")
    print("(the rational ranks) + grounded structure — NOT a from-scratch derivation.")
    print("The win is the RUNG climbed (the coefficient ring acquired) + the honest")
    print("read-vs-compute split + the honest distance, NOT the bordism answer (HLE")
    print("research-math correct stays ~0).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

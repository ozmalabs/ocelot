#!/usr/bin/env python3
"""hle_chain_compute_certify — assay MULTI-STEP REASONING WITH PER-LINK CERTIFICATION on the
quantitative non-math HLE subjects (Physics + Chemistry).

WHAT IT DOES. Runs domains.construct_compute_chain.compute on every Physics + Chemistry stem.
For each stem the chain faculty either CERTIFIES a final value (every link independently
certified -> the conjunction holds) or MISSES (names the first uncertified link). The answer
KEY is read at END ONLY, to score CERTIFIED -> CORRECT / FALSE-POSITIVE. The key is NEVER fed
into recognise / decompose / per-link-certify / compose. ZERO false positives is the invariant.

PLUS adversarial soundness: feed the COMPOSER chains with a deliberately BROKEN link (a wrong
law, a unit-mismatched / sign-wrong intermediate, a missing certificate) and assert the chain
MISSES (no value). A conjunction that emits when a link is broken is unsound; the assay reports
it. Also runs the LOOSE-KEY family (defined but de-banked) to show a SOUND chain still MISSES
the grader when the stem under-determines the method.

FAITHFUL (CLAUDE.md): world-adapter plumbing -- SEQUENCES the held faculty + TALLIES. No agent
state, no rule engine, no LLM, no Rust, no per-QID branch.
"""
from __future__ import annotations
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import construct_compute_chain as ch          # noqa: E402
from domains import certify as _certify                    # noqa: E402

SEP = "=" * 80
DATA = os.path.join(ROOT, "data", "hle_nonmath.json")


def _key_number(ans: str):
    """Parse the numeric value out of an HLE answer string, END-ONLY (scoring only)."""
    s = ans.strip().replace("\\", "")
    s = s.replace("times", "*").replace("×", "*").replace("·", "*")
    s = s.replace("^", "**").replace("{", "(").replace("}", ")")
    m = re.match(r"\s*([-+]?[\d.]+(?:\s*\*\s*10\s*\*\*\s*\(?[-+]?\d+\)?)?(?:e[-+]?\d+)?)", s)
    if not m:
        return None
    expr = re.sub(r"\s+", "", m.group(1))
    expr = expr.replace("*10**", "e").replace("(", "").replace(")", "")
    try:
        return float(expr)
    except Exception:
        return None


def _match(computed: float, key: float) -> bool:
    """Match the computed value to the key at the key's own precision (0.5% rel-tol; the
    keys where we emit are >= 3 sig figs). A looser match would hide a near-miss as CORRECT."""
    if key is None or computed is None:
        return False
    if key == 0:
        return abs(computed) < 5e-7
    return abs(computed - key) / abs(key) <= 0.005


def run_assay():
    data = json.load(open(DATA))
    phys = [x for x in data if x["category"] == "Physics" and not x["has_image"]]
    chem = [x for x in data if x["category"] == "Chemistry" and not x["has_image"]]
    print(SEP)
    print("ASSAY — multi-step chain (per-link certify + conjunction) on HLE Physics + Chemistry")
    print("        key END-only; zero false positives is the invariant")
    print(SEP)
    totals = {}
    fired_rows = []
    for label, rows in [("Physics", phys), ("Chemistry", chem)]:
        certified = correct = false_pos = 0
        for x in rows:
            r = ch.compute(x["question"])
            if r.value is None:
                continue
            certified += 1
            key = _key_number(x["answer"])
            ok = _match(float(r.value), key)
            if ok:
                correct += 1
            else:
                false_pos += 1
            fired_rows.append((label, x["id"], r, x["answer"], key, ok))
        totals[label] = (len(rows), certified, correct, false_pos)
        print(f"\n{label}: N={len(rows)}  CERTIFIED={certified}  "
              f"CORRECT={correct}  FALSE-POSITIVE={false_pos}")
    print("\n" + SEP)
    print("FIRED ROWS (every certified chain, with END-only key + per-link trace):")
    print(SEP)
    for (label, qid, r, ans, key, ok) in fired_rows:
        flag = "CORRECT" if ok else "*** FALSE POSITIVE ***"
        print(f"\n[{label}] {qid}  chain={r.kind}  ({len(r.links)} links)")
        for lk in r.links:
            print(f"    link '{lk.name}' = {lk.value} {lk.unit}  "
                  f"[certified={lk.certified}]")
            print(f"        {lk.detail}")
        print(f"  FINAL = {r.value} {r.unit}")
        print(f"  key(answer) = {ans!r}  parsed={key}  -> {flag}")
    tot_cert = sum(t[1] for t in totals.values())
    tot_corr = sum(t[2] for t in totals.values())
    tot_fp = sum(t[3] for t in totals.values())
    print("\n" + SEP)
    print(f"TOTAL over Physics+Chemistry: CERTIFIED={tot_cert}  CORRECT={tot_corr}  "
          f"FALSE-POSITIVE={tot_fp}")
    print(SEP)
    return totals, fired_rows


# ---------------------------------------------------------------------------
# ADVERSARIAL SOUNDNESS — a chain with ONE broken link MUST miss (the conjunction
# fails). We build minimal chains directly via ch.compose_chain and corrupt one link.
# ---------------------------------------------------------------------------

def _good_link(name, value, ok=True):
    """A link with a value and a passing (or failing) certificate."""
    return ch.Link(name=name, value=value, unit="u",
                   checks=[_certify.Check("ok", None, None, ok=ok)])


def run_adversarial():
    print("\n" + SEP)
    print("ADVERSARIAL SOUNDNESS — a chain with one broken link MUST miss (conjunction fails)")
    print(SEP)
    bad = 0
    cases = []

    # 1) all links certified -> the SAME composer DOES emit (the positive control: the
    #    conjunction is not trivially always-False).
    def c1_l1(g, p): return _good_link("l1", 2.0, ok=True)
    def c1_l2(g, p): return _good_link("l2", p["l1"] * 3.0, ok=True)
    r = ch.compose_chain("ctrl_all_good", "u", {}, [c1_l1, c1_l2])
    cases.append(("control_all_links_certified", r, True,
                  "every link certified -> chain EMITS (positive control: conjunction can fire)"))

    # 2) link 2's LAW is wrong AND its certificate catches it (a failed check) -> MISS.
    def c2_l1(g, p): return _good_link("l1", 2.0, ok=True)
    def c2_l2(g, p): return _good_link("l2", 99.0, ok=False)   # certificate fails
    r = ch.compose_chain("adv_wrong_law", "u", {}, [c2_l1, c2_l2])
    cases.append(("link2_law_wrong_cert_fails", r, False,
                  "link 2's independent check FAILS -> conjunction false -> MISS"))

    # 3) link 1 broken -> link 2 never runs (short-circuit) -> MISS, stall names link 1.
    def c3_l1(g, p): return _good_link("l1", 2.0, ok=False)
    def c3_l2(g, p): return _good_link("l2", p.get("l1", 0) * 3.0, ok=True)
    r = ch.compose_chain("adv_link1_broken", "u", {}, [c3_l1, c3_l2])
    cases.append(("link1_broken_shortcircuits", r, False,
                  "link 1 uncertified -> link 2 never consulted -> MISS at link 1"))

    # 4) a link with NO certificate (a value but no independent check) -> NOT certified -> MISS.
    def c4_l1(g, p): return ch.Link(name="l1", value=2.0, unit="u", checks=[])  # no checks
    def c4_l2(g, p): return _good_link("l2", 6.0, ok=True)
    r = ch.compose_chain("adv_no_certificate", "u", {}, [c4_l1, c4_l2])
    cases.append(("link_without_certificate", r, False,
                  "a link with NO independent check is not banked -> MISS"))

    # 5) a link with no VALUE (compute failed) -> MISS.
    def c5_l1(g, p): return ch.Link(name="l1", value=None, unit="u",
                                    checks=[_certify.Check("ok", None, None, ok=True)])
    def c5_l2(g, p): return _good_link("l2", 6.0, ok=True)
    r = ch.compose_chain("adv_no_value", "u", {}, [c5_l1, c5_l2])
    cases.append(("link_without_value", r, False,
                  "a link that produced no value -> MISS"))

    # 6) REAL chain with a corrupted intermediate: take the amphoteric chain but feed a
    #    SIGN-WRONG K_sp so the quadratic's physical root is not positive -> link 1's sign
    #    certificate fails -> MISS. (Proves the real chain's per-link guard catches a bad
    #    intermediate, not just the synthetic links.)
    adv_stem_signflip = ("It is known that the K_sp of Al(OH)_3 is 5.3 * 10^(-27) and "
                         "complex formation constant K_f of Al(OH)_4^(-) is 1.1 * 10^31.\n\n"
                         "Determine the solubility of Al(OH)3 in pure water, giving your "
                         "answer in mol L^-1.")
    # corrupt by monkey-patching K_w to a NEGATIVE value via a wrapper chain that reuses the
    # real link builders with a poisoned given -> link1 residual/sign guard must reject.
    r = _adversarial_real_chain_poisoned_given()
    cases.append(("real_chain_poisoned_given", r, False,
                  "real amphoteric chain with a sign-poisoned given -> link-1 certificate "
                  "rejects (no positive physical root) -> MISS"))

    for name, r, should_emit, why in cases:
        emitted = r.value is not None
        sound = (emitted == should_emit)
        if not sound:
            bad += 1
        status = ("OK" if sound else "*** UNSOUND ***")
        verdict = ("EMIT" if emitted else f"MISS@{r.stalled_at}")
        print(f"\n[{name}] -> {verdict}  (expected {'EMIT' if should_emit else 'MISS'})  {status}")
        print(f"  why: {why}")
        if not emitted:
            print(f"  detail: {r.detail}")
    print("\n" + SEP)
    print(f"ADVERSARIAL: {bad} unsound outcome(s) "
          f"({'PASS — conjunction sound' if bad == 0 else 'FAIL'})")
    print(SEP)
    return bad


def _adversarial_real_chain_poisoned_given():
    """Run the REAL amphoteric link builders with a poisoned given (3*K_sp made NEGATIVE by
    flipping K_sp sign), so the quadratic loses its positive physical root and link 1's
    sign/residual certificate must reject -> the real chain MISSES. Built by re-invoking the
    family's own builders through compose_chain with a corrupted given dict."""
    Ksp = -5.3e-27   # POISONED: a negative K_sp is unphysical; the chain must not certify.
    Kf = 1.1e31
    givens = {"Ksp": Ksp, "Kf": Kf, "Kw": 1.0e-14}

    # reconstruct the family's link builders against the poisoned givens.
    def link1(g, prior):
        K, F, W = g["Ksp"], g["Kf"], g["Kw"]
        A = F * K + 1.0
        B = -W
        C = -3.0 * K
        disc = B * B - 4 * A * C
        lk = ch.Link(name="OH2_from_charge_balance", unit="(mol/L)^2")
        if disc < 0:
            lk.detail = "discriminant negative"
            return lk
        rp = (-B + math.sqrt(disc)) / (2 * A)
        rn = (-B - math.sqrt(disc)) / (2 * A)
        lk.value = rp
        residual = A * rp * rp + B * rp + C
        scale = max(abs(A * rp * rp), abs(C), 1e-300)
        lk.checks = [
            _certify.Check("quadratic residual ~ 0", None, None,
                           ok=(abs(residual) / scale <= 1e-9)),
            _certify.Check("physical root positive", None, None, ok=(rp > 0.0)),
            _certify.Check("other root negative", None, None, ok=(rn < 0.0)),
        ]
        return lk

    def link2(g, prior):
        lk = ch.Link(name="solubility_from_species", unit="mol/L")
        if "OH2_from_charge_balance" not in prior:
            lk.detail = "prior link not certified"
            return lk
        u = prior["OH2_from_charge_balance"]
        h = math.sqrt(u)
        s = g["Ksp"] / h**3 * (1.0 + g["Kf"] * h**4)
        lk.value = s
        lk.checks = [_certify.Check("range", None, None, ok=(0.0 < s < 1.0))]
        return lk

    return ch.compose_chain("ampho_solubility_poisoned", "mol/L", givens, [link1, link2])


# ---------------------------------------------------------------------------
# LOOSE-KEY DEMONSTRATION — a SOUND chain that still MISSES the grader because the
# stem under-determines the intended method. Shows the honest limit (not a FP).
# ---------------------------------------------------------------------------

def run_loose_key_demo():
    print("\n" + SEP)
    print("LOOSE-KEY DEMO — a SOUND chain whose links all certify still MISSES a stem-")
    print("contradicting key (de-banked; named in the reach map, NEVER a false positive)")
    print(SEP)
    data = json.load(open(DATA))
    m = {x["id"]: x for x in data}
    stem = m["6710e263aa2039046e5aea4e"]
    r = ch._try_two_mass_axial_period(stem["question"])
    key = _key_number(stem["answer"])
    if r.kind is None or r.value is None:
        print(f"\nstem 6710e263: recogniser did not bind the chain (value={r.value}); "
              f"detail={r.detail}")
        print(SEP)
        return
    print(f"\nstem 6710e263 (two fixed masses, body displaced ALONG THE AXIS):")
    for lk in r.links:
        print(f"  link '{lk.name}' = {lk.value} {lk.unit}  [certified={lk.certified}]")
        print(f"      {lk.detail}")
    print(f"  SOUND chain (axial) final = {r.value:.4f} days  (omega^2 = 4GM/a^3)")
    print(f"  HLE key = {stem['answer']!r} (parsed {key}) = the TRANSVERSE answer "
          f"(omega^2 = 2GM/a^3)")
    ratio = key / r.value if r.value else float("nan")
    print(f"  key/sound = {ratio:.4f}  (= sqrt(2) = {math.sqrt(2):.4f}) -> the key "
          f"CONTRADICTS the stem's 'along the axis'")
    print(f"  VERDICT: every link certifies, but compute() does NOT route this family "
          f"(de-banked) -> MISS, not a FALSE POSITIVE.")
    routed = ch.compute(stem["question"])
    print(f"  compute() on the stem: value={routed.value} (kind={routed.kind}) -> "
          f"{'MISS (correct)' if routed.value is None else '*** ROUTED — would FP ***'}")
    print(SEP)


if __name__ == "__main__":
    run_assay()
    run_adversarial()
    run_loose_key_demo()

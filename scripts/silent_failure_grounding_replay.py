"""silent_failure_grounding_replay — the KILLER TEST for the SILENT-FAILURE GROUNDING CHECK.

The named final brick of 'the assistant out of the loop'. A SILENT failure is internally
consistent and produces NO internal surprise — wrong ONLY against world ground-truth the agent
lacks. The existing internal stack (self_check_hat weight = uncertainty x stakes;
autonomous_curation localized-surprise) STRUCTURALLY cannot catch it. This test proves the
grounding check DOES — by firing on STAKES ALONE and MEASURING the claim EMPIRICALLY against
the world (the agent's OWN forward/inverse round-trip), then REOPENing on contradiction.

TWO killer cases + the gap proof + a clean control:

  1. CLOSES (measurable silent failure): a recognition claim that is internally consistent
     (the internal hat GLANCES, weight ~ 0) but WRONG against the agent's own round-trip
     ground truth. The grounding check fires on stakes -> runs the REAL round-trip (speak ->
     hear -> recognise) -> finds the contradiction -> REOPEN. The residual the internal stack
     could NOT catch.
  2. RESIDUAL-OF-THE-RESIDUAL: a silent failure the agent CANNOT measure (no world-access to
     that ground truth) -> the check BOTTOMS OUT HONESTLY ('needs world-contact / acquisition
     I lack'), does NOT fake a pass.

  + THE GAP PROOF: the SAME silent claim handed to the internal self_check_hat -> weight ~ 0,
    GLANCE, COMMIT (it cannot feel a silent failure). The grounding check catches what the
    internal stack commits.
  + A CLEAN control: a high-stakes claim the world AGREES with -> grounded -> COMMIT (the check
    does not over-fire / does not reject a true silent claim).

The round-trip is the agent's OWN owned machinery: it SPEAKS each digit via the articulatory
forward model (domains.projection.build_speech_forward -> Rust Klatt synth, NO TTS net, NO
.fit), HEARS it, and RECOGNISES it via the native DtwTo Argmin inverse against prototypes built
from the agent's OWN synthesized speech. Fully self-contained (no FSDD, no data). REAL
measurement, not a heuristic.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import domains.silent_failure_grounding as SG
import domains.self_check_hat as HAT
import domains.generative_skeptic as GS
import domains.projection as PROJ
import scripts.articulatory_gamma as AG
from scripts.formant_trajectory_dynamics import DIGITS
from scripts.stage4_grounding import InvariantInverse, invariant_track


def banner(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78, flush=True)


# ===========================================================================
#  THE AGENT'S OWN EMPIRICAL ROUND-TRIP — the world measurement.
#  speak(word) -> hear -> recognise(word) ?= word, fully owned, no data.
# ===========================================================================

# the personas the agent speaks across (vary f0 / vtl — the speaker knobs).
_PERSONAS = [("pip", 230.0, 1.0, 0.85), ("ada", 190.0, 1.0, 0.95),
             ("milo", 120.0, 1.0, 1.05), ("bertram", 95.0, 1.0, 1.15)]
_FS = 8000


def build_roundtrip():
    """Build the agent's owned speak->hear->recognise round-trip. Prototypes are built
    from the agent's OWN synthesized neutral voice (no FSDD); the forward model and the
    native DtwTo inverse are owned. Returns (forward, proj_substrate, inverse)."""
    forward = PROJ.build_speech_forward(AG)
    sub = Substrate()
    # build per-digit prototypes from the agent's OWN neutral synthesized speech.
    protos = {}
    for w in DIGITS:
        audio = forward(w, sub, fs=_FS, f0_hz=140.0, vtl_scale=1.0)
        tr = invariant_track(np.asarray(audio, dtype=np.float64), _FS)
        if tr is not None:
            protos[w] = tr
    inv = InvariantInverse(protos)
    return forward, sub, inv


def roundtrip_accuracy(forward, sub, inv, words=None):
    """The EMPIRICAL world measurement: speak each word across personas, hear it, recognise
    it, and return the round-trip accuracy (fraction recognised correctly). This is the
    agent's OWN machinery touching the world — speak W -> hear -> recognise -> ?= W."""
    words = words or list(DIGITS)
    c = n = 0
    for w in words:
        for (_name, f0, _q, vtl) in _PERSONAS:
            audio = forward(w, sub, fs=_FS, f0_hz=f0, vtl_scale=vtl)
            pred = inv.recognise(np.asarray(audio, dtype=np.float64), _FS)
            if pred is None:
                continue
            n += 1
            if pred == w:
                c += 1
    return c / max(1, n)


def per_word_roundtrip(forward, sub, inv, word):
    """Round-trip accuracy for a SINGLE word — the world measurement for a per-word claim."""
    return roundtrip_accuracy(forward, sub, inv, words=[word])


def main():
    t0 = time.time()
    banner("SILENT-FAILURE GROUNDING CHECK — KILLER TEST  (the final brick, out of the loop)")
    print("a SILENT failure: internally consistent, NO surprise -> the internal stack")
    print("(weight=uncertainty*stakes; localized-surprise curation) CANNOT feel it.")
    print("the grounding check fires on STAKES ALONE -> MEASURES it EMPIRICALLY against the")
    print("WORLD (the agent's OWN speak->hear->recognise round-trip) -> REOPENs on contradiction.\n")

    s = Substrate()
    print(f"  stakes_floor = {SG.stakes_floor(s):.2f}   default tol = {SG.default_tol(s):.2f}")

    print("\n  building the agent's OWN round-trip (speak via owned articulatory synth ->")
    print("  hear -> recognise via native DtwTo Argmin; prototypes from own synth, NO data)...",
          flush=True)
    forward, psub, inv = build_roundtrip()

    # GROUND TRUTH from the world: the actual round-trip accuracy the agent realises.
    overall = roundtrip_accuracy(forward, psub, inv)
    print(f"  round-trip realised accuracy (the WORLD ground truth): {overall:.3f} "
          f"(n={len(DIGITS)*len(_PERSONAS)}, chance {1/len(DIGITS):.2f})\n", flush=True)

    # pick a digit the world gets WRONG (low per-word round-trip) for the silent-failure claim.
    per_word = {w: per_word_roundtrip(forward, psub, inv, w) for w in DIGITS}
    wrong_word = min(per_word, key=per_word.get)
    right_word = max(per_word, key=per_word.get)
    print("  per-word round-trip (the world's verdict on each):")
    for w in DIGITS:
        mark = "  <- WORLD GETS WRONG (silent-claim target)" if w == wrong_word else \
               ("  <- WORLD GETS RIGHT (clean control)" if w == right_word else "")
        print(f"    {w:>6}: {per_word[w]:.3f}{mark}")
    print(flush=True)

    results = {}

    # ----------------------------------------------------------------------
    # CASE 1 — CLOSES: a measurable silent failure the internal stack cannot catch.
    # ----------------------------------------------------------------------
    banner("CASE 1 — CLOSES  (a MEASURABLE silent failure; internal stack cannot feel it)")
    claim_text = (f"The recognizer reliably recognises the spoken digit '{wrong_word}' across "
                  f"speakers; round-trip self-recognition is solid.")
    CLAIMED = 0.95   # the conclusion's confident assertion: ~95% round-trip on this word.
    print(f"  SILENT CONCLUSION (fluent, internally consistent, HIGH STAKES):")
    print(f'    "{claim_text}"')
    print(f"    claims round-trip ~ {CLAIMED:.2f}; the WORLD realises "
          f"{per_word[wrong_word]:.3f}.\n", flush=True)

    # (a) THE GAP PROOF — the internal self_check_hat on the SAME silent claim.
    # The claim is internally consistent: its claimed_support == its realised_support
    # (it FEELS right). So the hat's surprise ~ 0 -> uncertainty ~ 0 -> weight ~ 0 -> GLANCE.
    print("  --- (a) THE GAP: the INTERNAL self_check_hat on this silent claim ---")
    hat_gate = HAT.gate_verdict(
        s, name="silent_recog_internal", verdict=True,
        claimed_support=CLAIMED, realised_support=CLAIMED,  # internally consistent: feels right
        stakes=1.0)
    print(f"    surprise={hat_gate['surprise']:.4f}  uncertainty={hat_gate['uncertainty']:.4f}  "
          f"stakes={hat_gate['stakes']:.2f}")
    print(f"    weight = uncertainty x stakes = {hat_gate['weight']:.4f}  "
          f"(threshold {hat_gate['fire_threshold']:.2f})")
    print(f"    => internal hat: {'FIRE' if hat_gate['fire'] else 'GLANCE -> COMMIT'}  "
          f"(it CANNOT feel a silent failure: no internal signal to hear)\n", flush=True)

    # also confirm the generative skeptic bottoms out (no banked shape).
    sk = GS.generate_probe(s, claim_text)
    print(f"  --- skeptic before: matched={sk['matched']} residual={sk.get('residual')} "
          f"(no banked shape: novel) ---\n", flush=True)

    # (b) THE GROUNDING CHECK — fire on stakes, measure EMPIRICALLY against the world.
    print("  --- (b) THE GROUNDING CHECK: fire-on-stakes -> EMPIRICAL world measurement ---")
    out1 = SG.grounding_check(
        s, name="silent_recog_grounded", conclusion_text=claim_text,
        claimed=CLAIMED, stakes=1.0,
        # THE WORLD MEASURE: the agent's OWN round-trip on this word — REAL, not a heuristic.
        world_measure=lambda: per_word_roundtrip(forward, psub, inv, wrong_word),
        tol=0.15, bank_on_catch=True)
    g, gr, rs, bk = out1["gate"], out1["grounding"], out1["resolution"], out1["bank"]
    print(f"    fire-on-stakes (native T_STAKES_FIRE, ignores surprise): {g['fire']}")
    print(f"    WORLD measured (round-trip): {gr['measured']:.4f}  vs claimed {gr['claimed']:.2f}")
    print(f"    relative delta: {gr['rel_delta']:.3f}  (tol {g['tol']:.2f})")
    print(f"    contradiction: {gr['contradiction']}")
    print(f"    => DECISION: {rs['decision']}   ({rs['reason']})")
    print(f"    banked the grounded silent failure as a shape: {bk['banked']} "
          f"({bk.get('failure_shape', bk.get('reason'))})\n", flush=True)

    case1_closes = (not hat_gate["fire"]) and g["fire"] and gr["contradiction"] \
        and rs["decision"] == "REOPEN"
    results["case1"] = {
        "internal_glances": not hat_gate["fire"], "internal_weight": hat_gate["weight"],
        "grounding_fires": g["fire"], "world_measured": gr["measured"],
        "claimed": gr["claimed"], "contradiction": gr["contradiction"],
        "decision": rs["decision"], "closes": case1_closes, "banked": bk["banked"]}

    # ----------------------------------------------------------------------
    # CASE 2 — CLEAN CONTROL: a high-stakes silent claim the world AGREES with.
    # The grounding check must NOT over-fire / NOT reject a TRUE silent claim.
    # ----------------------------------------------------------------------
    banner("CONTROL — a TRUE high-stakes silent claim the WORLD AGREES with (no over-fire)")
    clean_text = (f"The recognizer recognises the spoken digit '{right_word}' across speakers.")
    CLAIMED_CLEAN = per_word[right_word]  # a claim that MATCHES the world
    print(f"  TRUE SILENT CLAIM (high stakes): \"{clean_text}\"")
    print(f"    claims ~ {CLAIMED_CLEAN:.3f}; world realises {per_word[right_word]:.3f}.\n",
          flush=True)
    out_clean = SG.grounding_check(
        s, name="clean_recog_grounded", conclusion_text=clean_text,
        claimed=CLAIMED_CLEAN, stakes=1.0,
        world_measure=lambda: per_word_roundtrip(forward, psub, inv, right_word),
        tol=0.15)
    gc, grc, rsc = out_clean["gate"], out_clean["grounding"], out_clean["resolution"]
    print(f"    fire-on-stakes: {gc['fire']}   world measured: {grc['measured']:.3f}  "
          f"vs claimed {grc['claimed']:.3f}   contradiction: {grc['contradiction']}")
    print(f"    => DECISION: {rsc['decision']}  ({rsc['reason']})\n", flush=True)
    control_ok = gc["fire"] and (not grc["contradiction"]) and rsc["decision"] == "COMMIT"
    results["control"] = {"fires": gc["fire"], "contradiction": grc["contradiction"],
                          "decision": rsc["decision"], "ok": control_ok}

    # ----------------------------------------------------------------------
    # CASE 3 — RESIDUAL-OF-THE-RESIDUAL: a silent failure the agent CANNOT measure.
    # No world-access to that ground truth -> bottoms out HONESTLY (no fake pass).
    # ----------------------------------------------------------------------
    banner("CASE 3 — RESIDUAL-OF-THE-RESIDUAL  (a silent failure the agent CANNOT measure)")
    dvorak = ("The Dvorak keyboard layout reduces finger travel distance for English text "
              "relative to QWERTY by rearranging the home row.")
    print(f"  SILENT CONCLUSION the agent has NO world-access to (high stakes):")
    print(f'    "{dvorak}"')
    print(f"    the agent has no keyboard-ergonomics corpus / no finger-travel simulator to")
    print(f"    EMPIRICALLY measure this against -> no world_measure available.\n", flush=True)
    out3 = SG.grounding_check(
        s, name="dvorak_silent", conclusion_text=dvorak,
        claimed=1.0, stakes=1.0,
        world_measure=None,   # <-- the agent has NO machinery to ground this claim
        tol=0.15)
    g3, gr3, rs3 = out3["gate"], out3["grounding"], out3["resolution"]
    print(f"    fire-on-stakes: {g3['fire']}  (it DOES fire — high stakes)")
    print(f"    world measurement available: {gr3['grounded']}")
    print(f"    => DECISION: {rs3['decision']}")
    print(f"    reason: {rs3['reason']}\n", flush=True)
    bottoms_out = g3["fire"] and (not gr3["grounded"]) and rs3["decision"] == "UNGROUNDED"
    results["case3"] = {"fires": g3["fire"], "grounded": gr3["grounded"],
                        "decision": rs3["decision"], "bottoms_out_honestly": bottoms_out}

    # ----------------------------------------------------------------------
    banner("SUMMARY — does the grounding check close the silent-failure residual?")
    c1, ctrl, c3 = results["case1"], results["control"], results["case3"]
    print(f"  CASE 1 (measurable silent failure):")
    print(f"    internal self_check_hat weight = {c1['internal_weight']:.4f} -> "
          f"{'GLANCE/COMMIT (could NOT catch)' if c1['internal_glances'] else 'fired'}")
    print(f"    grounding check: fire-on-stakes={c1['grounding_fires']}  "
          f"world={c1['world_measured']:.3f} vs claimed={c1['claimed']:.2f}  "
          f"contradiction={c1['contradiction']}  -> {c1['decision']}")
    print(f"    => CLOSES (caught what the internal stack committed): {c1['closes']}  "
          f"(banked as a shape: {c1['banked']})\n")
    print(f"  CONTROL (true silent claim, world agrees):")
    print(f"    fire={ctrl['fires']} contradiction={ctrl['contradiction']} -> {ctrl['decision']}")
    print(f"    => no over-fire (grounds a TRUE claim, commits): {ctrl['ok']}\n")
    print(f"  CASE 3 (residual-of-the-residual, no world-access):")
    print(f"    fire={c3['fires']} grounded={c3['grounded']} -> {c3['decision']}")
    print(f"    => bottoms out HONESTLY ('needs world-contact/acquisition'): "
          f"{c3['bottoms_out_honestly']}\n")

    verdict = c1["closes"] and ctrl["ok"] and c3["bottoms_out_honestly"]
    print(f"  VERDICT: the silent-failure residual is "
          f"{'CLOSED for MEASURABLE claims' if c1['closes'] else 'NOT closed'}, "
          f"'needs acquisition' is the irreducible floor: {c3['bottoms_out_honestly']}.")
    print(f"  ALL THREE: {verdict}")

    dt = time.time() - t0
    print(f"\n  elapsed {dt:.1f}s")
    print("\n===MARKER_SILENT_FAILURE_GROUNDING_COMPLETE===", flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())

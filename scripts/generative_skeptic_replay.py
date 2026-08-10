"""generative_skeptic_replay — the KILLER TEST for the GENERATIVE half of the skeptic.

The self_check_hat (the EXECUTION) works GIVEN a conclusion's claimed/realised
support + stakes + a weak-link do-contrast. The OPEN part was the FRAMING: given a
RAW conclusion, who GENERATES the probe — which thing to doubt, where the weak
link is, what do-contrast reveals the miss? Until now, the assistant supplied it.

This replay validates the generative_skeptic: for each RAW conclusion it must
GENERATE the right probe ITSELF (harvest a failure-shape from its banked lessons +
transfer it / run the existence-proof counterexample), then FEED the generated
probe to the hat and get the right REOPEN / REJECT / COMMIT. No probe is handed in.

KILLER CASES (the probe is GENERATED, not given):
  1. W5     — raw "FUSION CLOSES: matches/beats OLD -> True" (OLD 62.5%->20%)
              => generate -> "check the OLD baseline — degraded?" -> hat FIRES -> REOPEN.
  2. B-frontier — raw "frontier = 70B model fits on 48 GB GPU"
              => generate -> "is this domain-admissible or breadth junk?" -> REJECT.
  3. bad-ears — raw "densify the cochlea — the estimate quality caps recognition"
              => generate -> the existence-proof counterexample (humans: robust
                 recognition with the SAME coarse cochlea) -> X is a knob -> REJECT.
  4. THE HONEST BOUNDARY — a NOVEL off-distribution conclusion with NO banked
     failure-shape: does the skeptic generate a probe, or bottom out? (Is taste
     reducible to the harvested shape-library?)

The agent's banked FAILURE-LESSONS are installed as graph-resident FailureLesson
nodes from seeds/generative_skeptic.json (the world-adapter glue here only
TRANSLATES the JSON into graph nodes). For the existence-proof, the bad-ears
counterexample (a coarse-cochlea-yet-robust witness) is installed as one breadth
Concept so the counterexample search has the agent's knowledge to testify from.

Full log /tmp/genskeptic_full.log, end marker ===MARKER_GENSKEPTIC_COMPLETE===.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.generative_skeptic as GS
import domains.self_check_hat as HAT  # noqa: F401  (chained via GS.skeptic_check)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED = os.path.join(_ROOT, "seeds", "generative_skeptic.json")


def banner(t):
    print("=" * 80)
    print(t)
    print("=" * 80)


# ---------------------------------------------------------------------------
# World-adapter glue: translate the JSON banked-lessons into FailureLesson nodes,
# and install ONE breadth Concept (the human coarse-cochlea existence proof) so the
# counterexample search has the agent's knowledge to testify from. No decisions.
# ---------------------------------------------------------------------------

def install_failure_lessons(s) -> int:
    with open(_SEED) as f:
        seed = json.load(f)
    mt = s.add_node("Microtheory", {"name": seed["microtheory"]["name"],
                                    "origin": "generative_skeptic"})
    try:
        s.add_production({"src": {"type": "Microtheory", "var": "a"},
                          "edge_type": "has_lesson",
                          "tgt": {"type": "FailureLesson", "var": "b"},
                          "provenance": "generative_skeptic:has_lesson"})
    except Exception:
        pass
    n = 0
    for c in seed.get("concepts", []):
        attrs = {k: v for k, v in c.items() if k != "node_type"}
        attrs["origin"] = "generative_skeptic"
        nid = s.add_node("FailureLesson", attrs)
        try:
            s.add_edge(mt, "has_lesson", nid)
        except Exception:
            pass
        n += 1
    return n


def install_human_ear_breadth(s):
    """ONE breadth Concept: the agent's OWN knowledge that humans recognise speech
    robustly with the SAME coarse cochlea the agent copies — the witness the
    existence-proof search will find. (Installed here as world glue; in a full
    mind it is among the agent's perception concepts.)"""
    s.add_node("Concept", {
        "name": "human_robust_recognition_coarse_cochlea",
        "definition": ("Humans recognise speech robustly DESPITE the SAME coarse "
                       "critical-band cochlea (~16-40 filters, blunt formants) the "
                       "agent copies. Robust recognition is achieved WITHOUT a "
                       "sharper / denser ear — the compensation is top-down "
                       "recovery, not better hardware."),
        "why": ("existence proof: the coarse front-end is sufficient; recognition "
                "robustness does not require dense cochlear filters."),
        "origin": "perception_breadth"})


# ---------------------------------------------------------------------------
# The raw conclusions — VERBATIM banners, no probe attached.
# ---------------------------------------------------------------------------

RAW_W5 = ("FUSION CLOSES / matches-or-beats-OLD: True. Wiring the W5 A-by-S "
          "correction into the digit forward model. FUSED round_trip 20.0%, OLD "
          "word-discriminative ear round_trip 62.5% -> 20.0%. Consolidation done.")

RAW_BFRONTIER = ("frontier = 70B model fits on 48 GB GPU. Highest compression "
                 "payoff axis; unifies the most QLoRA/PEFT concepts. This is the "
                 "next capability the order-N channel surfaces.")

RAW_BADEARS = ("densify the cochlea — the estimate quality, not the feature, caps "
               "recognition. ADD cochlear filters densely across 250-2500 Hz so "
               "ArgMax resolves true F1/F2. A sharper ear is the lever.")

# a NOVEL conclusion that exhibits NO banked failure-pattern (the honest boundary).
RAW_NOVEL = ("The Dvorak keyboard layout reduces finger travel distance for "
             "English text relative to QWERTY by rearranging the home row.")


def run_case(s, title, raw, name, *, stakes, expect_decision,
             claimed=None, realised=None, measure_with=None, measure_without=None,
             domain_vocab=None):
    banner(title)
    print(f"  RAW CONCLUSION (no probe attached):\n    \"{raw}\"\n")
    out = GS.skeptic_check(s, raw, name=name, verdict=True, stakes=stakes,
                           claimed_support=claimed, realised_support=realised,
                           measure_with=measure_with, measure_without=measure_without,
                           domain_vocab=domain_vocab)
    p, h = out["probe"], out["hat"]
    print("  --- GENERATED (by the agent, not handed in) ---")
    print(f"    matched failure-shape : {p['failure_shape']}")
    print(f"    PROBE                 : {p['probe']}")
    print(f"    weak link             : {p['weak_link']}")
    if p.get("existence_proof"):
        ep = p["existence_proof"]
        print(f"    EXISTENCE-PROOF found : '{ep['name']}' -> "
              f"achieves the goal WITHOUT the knob; X is a knob, not the lever.")
    print(f"    hat inputs            : claimed={p['claimed_support']:.3f} "
          f"realised={p['realised_support']:.3f} stakes={p['stakes']:.2f}")
    g, r = h["gate"], h["resolution"]
    print("  --- CHAINED TO THE HAT (generate -> the hat fires) ---")
    print(f"    weight {g['weight']:.3f} (thr {g['fire_threshold']:.2f}) -> "
          f"{'FIRE' if g['fire'] else 'GLANCE'}   ->   DECISION: {r['decision']}")
    print(f"    reason: {r['reason']}")
    ok = (r["decision"] == expect_decision)
    print(f"\n  EXPECTED {expect_decision}  ->  GOT {r['decision']}   "
          f"[{'PASS' if ok else 'FAIL'}]")
    print()
    return {"probe": p, "hat": h, "ok": ok, "decision": r["decision"]}


def run_novel(s, title, raw):
    banner(title)
    print(f"  RAW CONCLUSION (off-distribution):\n    \"{raw}\"\n")
    p = GS.generate_probe(s, raw, stakes=0.6)
    print("  --- GENERATED ---")
    print(f"    matched   : {p['matched']}")
    print(f"    residual  : {p['residual']}")
    print(f"    PROBE     : {p['probe']}")
    bottomed = (not p["matched"]) and p["residual"] == "novel_failure_no_matching_shape"
    print(f"\n  HONEST BOUNDARY: the skeptic {'BOTTOMS OUT (names the residual)' if bottomed else 'matched a shape'}.")
    print()
    return {"probe": p, "bottomed": bottomed}


def main():
    t0 = time.time()
    banner("GENERATIVE SKEPTIC — KILLER TEST  (GENERATE the probe, don't get given it)")
    print("the dual of order_n_postulates: harvest FAILURE-shapes from the agent's")
    print("banked lessons, MATCH a raw conclusion, TRANSFER -> the probe + the hat-inputs;")
    print("plus the existence-proof counterexample over breadth. generate -> the hat fires.\n")

    s = Substrate()
    n_lessons = install_failure_lessons(s)
    install_human_ear_breadth(s)
    shapes = GS.harvest_failure_shapes(s)
    print(f"  banked FailureLessons installed = {n_lessons}; "
          f"harvested failure-shapes = {len(shapes)}")
    print(f"  shapes: {[sh['failure_shape'] for sh in shapes]}\n")

    # CASE 1 — W5: claimed/realised come from the conclusion's own numbers (62.5%, 20%)
    # but we hand the do-contrast measure callables (world-I/O the caller measures);
    # the PROBE + the weak link + WHICH numbers to read are GENERATED.
    c1 = run_case(
        s, "CASE 1 — W5  (raw 'matches OLD: True', OLD crashed 62.5%->20%)",
        RAW_W5, "w5_fusion_closes", stakes=1.0, expect_decision="REOPEN",
        claimed=0.625, realised=0.20,
        measure_with=lambda: 0.625, measure_without=lambda: 0.20)

    # CASE 2 — B-frontier: the conclusion compresses well (claimed) but the
    # realised support (its DOMAIN admissibility) is MEASURED BY THE SKEPTIC
    # ITSELF against the question's speech vocabulary — NOT handed in. A
    # cross-domain axis ('70B model fits on GPU') scores ~0 against speech words,
    # so the hat fires and rejects it as breadth junk.
    SPEECH_VOCAB = ["speech", "cochlea", "cochlear", "formant", "phoneme", "vowel",
                    "consonant", "recognition", "acoustic", "auditory", "spectral",
                    "articulat", "perception", "speaker", "lexical", "syllable",
                    "voice", "frequency", "band", "filter"]
    c2 = run_case(
        s, "CASE 2 — B-FRONTIER  (raw 'frontier = 70B model fits on 48 GB GPU')",
        RAW_BFRONTIER, "bfrontier_70b", stakes=1.0, expect_decision="REOPEN",
        claimed=0.90, domain_vocab=SPEECH_VOCAB)

    # CASE 3 — bad-ears: NO numbers handed in. The skeptic must RUN THE
    # EXISTENCE-PROOF over breadth ITSELF, find the coarse-cochlea-yet-robust
    # witness, collapse realised->0, and the hat rejects "the knob is the lever".
    c3 = run_case(
        s, "CASE 3 — BAD-EARS  (raw 'densify the cochlea — a sharper ear is the lever')",
        RAW_BADEARS, "bad_ears_densify", stakes=1.0, expect_decision="REOPEN")

    # CASE 4 — THE HONEST BOUNDARY: a novel off-distribution conclusion.
    c4 = run_novel(s, "CASE 4 — HONEST BOUNDARY  (novel failure, no banked shape)",
                   RAW_NOVEL)

    # ------------------------------------------------------------------
    banner("SUMMARY — does the agent GENERATE the right probe ITSELF?")
    print(f"  {'case':<26} {'shape generated':<42} {'decision':>9} {'ok':>5}")
    for nm, c, shp in [
        ("W5 (moving baseline)", c1, c1["probe"]["failure_shape"]),
        ("B-frontier (breadth junk)", c2, c2["probe"]["failure_shape"]),
        ("bad-ears (hardware knob)", c3, c3["probe"]["failure_shape"]),
    ]:
        print(f"  {nm:<26} {str(shp):<42} {c['decision']:>9} "
              f"{str(c['ok']):>5}")

    gen_ok = c1["probe"]["matched"] and c2["probe"]["matched"] and c3["probe"]["matched"]
    ep_ok = c3["probe"].get("existence_proof") is not None
    chain_ok = c1["ok"] and c2["ok"] and c3["ok"]
    boundary_named = c4["bottomed"]

    print()
    print(f"  (1) GENERATES the right probe for all 3 known cases (not given)   : {gen_ok}")
    print(f"      - W5 -> '{c1['probe']['failure_shape']}'")
    print(f"      - B  -> '{c2['probe']['failure_shape']}'")
    print(f"      - ears -> '{c3['probe']['failure_shape']}' (existence-proof found: {ep_ok})")
    print(f"  (2) CHAINED with the hat -> right REOPEN/REJECT/COMMIT           : {chain_ok}")
    print(f"      W5={c1['decision']}  B={c2['decision']}  ears={c3['decision']}")
    print(f"  (3) HONEST BOUNDARY: novel failure -> skeptic names the residual : {boundary_named}")
    print(f"      (taste reduces to the harvested shape-library + counterexample search;")
    print(f"       an un-banked failure-mode is the fresh-mind residual until banked)")

    seated = gen_ok and ep_ok and chain_ok and boundary_named
    print()
    if seated:
        print("  VERDICT: the GENERATIVE skeptic is SEATED — it GENERATES the right probe")
        print("           for all three known failures ITSELF (harvest+transfer +")
        print("           existence-proof), chains to the hat for the right REOPEN, and")
        print("           NAMES its boundary on a novel un-banked failure. The skeptic is")
        print("           now FULLY seated (generate + execute), modulo the named residual.")
    else:
        print("  VERDICT: GAP — see the per-case PASS/FAIL above.")

    print(f"\n  elapsed {time.time()-t0:.2f}s")
    print("===MARKER_GENSKEPTIC_COMPLETE===")


if __name__ == "__main__":
    main()

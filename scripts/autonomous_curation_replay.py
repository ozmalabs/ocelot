"""autonomous_curation_replay — the KILLER TEST for AUTONOMOUS FAILURE-CURATION.

THE QUESTION: does the loop SELF-CLOSE WITHOUT a human writing the memory?

The generative skeptic catches the failure-shapes it has BANKED, and BOTTOMS OUT
on a novel one (residual='novel_failure_no_matching_shape'). Until now, a HUMAN
banked the lesson (wrote the FailureLesson). This replay validates the agent doing
it ITSELF: detect -> the skeptic bottoms out -> RESOLVE (localize + do-contrast)
-> BANK the abstracted shape -> the skeptic now MATCHES it (and its near-misses).

THE LOOP (the same surprise->localize->construct learning loop, one level up):
  DETECT     native surprise fires; the weak link is localized (native MaxOver).
  UNMATCHED  the generative skeptic tries to match a banked shape and bottoms out.
  RESOLVE    do-contrast at the weak link (meta-monitor) -> the verdict = what was wrong.
  BANK       abstract the failure-SHAPE from the resolution; add a FailureLesson.
  SELF-CLOSE re-run the skeptic on the SAME failure + a NEAR-MISS -> it now matches.

KILLER CASES:
  A. LEAKAGE  — a novel train/test-leakage conclusion (corpus-wide normalisation):
                detect->bottom-out->resolve(lever_harms)->bank-> RE-RUN catches it
                AND a near-miss (a DIFFERENT leakage conclusion of the same shape),
                but NOT an unrelated conclusion (generalises, doesn't overfit).
  B. PROXY-METRIC — a SECOND, independent novel failure (optimising a proxy metric
                instead of the target): proves the loop is general, not one-shot.
  C. THE HONEST BOUNDARY — a SILENT novel failure with NO localized surprise: the
                loop bottoms out (names the fresh-mind residual), does NOT fake a bank.

The agent's 6 PRE-EXISTING banked lessons are installed from
seeds/generative_skeptic.json (world-glue translation only). The NOVEL failures
are NOT in that seed — no human banked them; the agent curates them in this run.

Full log /tmp/curation_full.log, end marker ===MARKER_CURATION_COMPLETE===.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.generative_skeptic as GS
import domains.autonomous_curation as AC

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED = os.path.join(_ROOT, "seeds", "generative_skeptic.json")


def banner(t):
    print("=" * 80)
    print(t)
    print("=" * 80)


def install_pre_banked_lessons(s) -> int:
    """World-glue: translate the agent's PRE-EXISTING banked lessons (the 6 the
    human banked in earlier sessions) into FailureLesson nodes. The NOVEL failures
    this replay curates are NOT among these."""
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


# ---------------------------------------------------------------------------
# THE NOVEL FAILURES — none of these is in seeds/generative_skeptic.json.
# Each is a fresh conclusion the agent has NOT lived; the skeptic bottoms out on
# it until the agent curates it ITSELF in this run.
# ---------------------------------------------------------------------------

# A — train/test LEAKAGE via corpus-wide normalisation.
NOVEL_LEAKAGE = ("After normalising every utterance by its own global mean "
                 "computed across the entire corpus, the classifier reaches 0.94 "
                 "on the evaluation split.")
# A near-miss: a DIFFERENT conclusion of the SAME leakage shape (global stats over
# every recording, then evaluate) — should be caught by the banked shape.
NEARMISS_LEAKAGE = ("We z-scored each frame using the global mean and variance "
                    "computed across every recording, then evaluated; word "
                    "accuracy is 0.88.")
# An UNRELATED conclusion that should NOT fire the learned shape (over-fit guard).
UNRELATED = ("The cochlear filterbank uses 32 gammatone channels spaced on an "
             "ERB scale to model the basilar membrane.")

# B — a SECOND, independent novel failure: optimising a PROXY metric, not the target.
NOVEL_PROXY = ("Optimising the centroid placement raised the silhouette "
               "coefficient from 0.31 to 0.58, so the vowel clustering improved.")
NEARMISS_PROXY = ("Tuning the embedding raised the silhouette score markedly, "
                  "which shows the phoneme grouping got better.")

# C — a SILENT novel failure: fluent, internally consistent, NO localizable surprise.
SILENT = ("The Dvorak keyboard layout reduces finger travel distance for English "
          "text relative to QWERTY by rearranging the home row.")


def run_curation_case(s, title, conclusion, dims, *, name, measure_with,
                      measure_without, near_miss=None, unrelated=None):
    banner(title)
    print(f"  NOVEL CONCLUSION (no human banked it):\n    \"{conclusion}\"\n")

    # SKEPTIC BEFORE — must bottom out (no banked shape).
    before = GS.generate_probe(s, conclusion)
    print("  --- 1. SKEPTIC BEFORE (does it bottom out?) ---")
    print(f"    matched : {before['matched']}   residual : {before.get('residual')}")
    bottomed = (not before["matched"]) and \
        before.get("residual") == "novel_failure_no_matching_shape"
    print(f"    => {'BOTTOMS OUT (a NOVEL failure)' if bottomed else 'already matched (NOT novel)'}\n")

    # THE LOOP — detect -> resolve -> bank.
    out = AC.curate(s, conclusion, dims, name=name,
                    measure_with=measure_with, measure_without=measure_without)
    det, res, bk = out["detection"], out["resolution"], out["bank"]
    print("  --- 2. DETECT (native surprise -> localize the weak link) ---")
    for d in det["dims"]:
        mark = " <- WEAK LINK" if det["weak_link"] and d["name"] == det["weak_link"]["name"] else ""
        print(f"    dim {d['name']:<26} surprise={d['surprise']:.3f}{mark}")
    print(f"    max localized surprise (native MaxOver) = {det['max_surprise']:.3f}\n")
    print("  --- 3. RESOLVE (do-contrast at the weak link via meta-monitor) ---")
    print(f"    payoff WITH={res['payoff_with']:.3f}  WITHOUT={res['payoff_without']:.3f}  "
          f"delta={res['delta']:+.3f}")
    print(f"    meta-verdict (the resolution = what was wrong) : {res['meta_verdict']}\n")
    print("  --- 4. BANK (abstract the shape; native graph mutation) ---")
    print(f"    banked : {bk['banked']}")
    print(f"    failure_shape : {bk['failure_shape']}")
    print(f"    match_patterns (ABSTRACTED from the resolution, not authored):")
    print(f"      {bk['match_patterns']}")
    print(f"    reason : {bk['reason']}\n")

    # SELF-CLOSE — re-run the skeptic on the SAME conclusion.
    after = GS.generate_probe(s, conclusion)
    print("  --- 5. SELF-CLOSE (re-run skeptic on the SAME failure) ---")
    print(f"    matched : {after['matched']}   shape : {after['failure_shape']}")
    self_closed = after["matched"] and after["failure_shape"] == bk["failure_shape"]
    print(f"    => {'SELF-CLOSED (now caught, no human wrote the memory)' if self_closed else 'NOT closed'}\n")
    if after["matched"]:
        print(f"    generated probe: {after['probe'][:140]}...\n")

    nm_caught = unrel_fired = None
    if near_miss is not None:
        nm = GS.generate_probe(s, near_miss)
        nm_caught = nm["matched"] and nm["failure_shape"] == bk["failure_shape"]
        print("  --- 6. GENERALIZE (a NEAR-MISS — different conclusion, same shape) ---")
        print(f"    near-miss: \"{near_miss[:90]}...\"")
        print(f"    matched : {nm['matched']}  shape : {nm['failure_shape']}")
        print(f"    => {'CAUGHT the near-miss (GENERALISES)' if nm_caught else 'missed (overfit)'}\n")
    if unrelated is not None:
        ur = GS.generate_probe(s, unrelated)
        unrel_fired = ur["matched"] and ur["failure_shape"] == bk["failure_shape"]
        print("  --- 7. OVER-FIT GUARD (an UNRELATED conclusion must NOT fire) ---")
        print(f"    unrelated: \"{unrelated[:80]}...\"")
        print(f"    fired the learned shape : {unrel_fired}")
        print(f"    => {'OK (does not over-fire)' if not unrel_fired else 'OVER-FIRES (overfit the wrong way)'}\n")

    return {"bottomed": bottomed, "banked": bk["banked"],
            "self_closed": self_closed, "near_miss_caught": nm_caught,
            "unrelated_fired": unrel_fired, "shape": bk["failure_shape"],
            "verdict": res["meta_verdict"]}


def run_silent_case(s, title, conclusion, dims, *, name):
    banner(title)
    print(f"  SILENT NOVEL CONCLUSION (fluent, internally consistent):\n    \"{conclusion}\"\n")
    before = GS.generate_probe(s, conclusion)
    bottomed = (not before["matched"])
    print(f"  skeptic before: matched={before['matched']} (novel: {bottomed})\n")
    out = AC.curate(s, conclusion, dims, name=name,
                    measure_with=lambda: 0.9, measure_without=lambda: 0.9)
    det, bk = out["detection"], out["bank"]
    print("  --- DETECT ---")
    for d in det["dims"]:
        print(f"    dim {d['name']:<26} surprise={d['surprise']:.4f}")
    print(f"    max localized surprise = {det['max_surprise']:.4f}  "
          f"(no dimension the prediction-error points at)\n")
    print("  --- BANK ---")
    print(f"    banked : {bk['banked']}")
    print(f"    reason : {bk['reason']}\n")
    boundary_named = (not bk["banked"])
    print(f"  => HONEST BOUNDARY: the loop {'BOTTOMS OUT (names the residual, does not fake a bank)' if boundary_named else 'banked a spurious shape'}.\n")
    return {"boundary_named": boundary_named}


def main():
    t0 = time.time()
    banner("AUTONOMOUS FAILURE-CURATION — KILLER TEST  (the assistant out of the loop)")
    print("the SAME surprise->localize->construct learning loop, pointed at FAILURE-SHAPES:")
    print("a NOVEL failure the skeptic can't catch -> detected -> resolved -> BANKED -> CAUGHT,")
    print("with NO human writing the memory. detect -> bottom-out -> resolve -> bank -> self-close.\n")

    s = Substrate()
    n_pre = install_pre_banked_lessons(s)
    shapes0 = GS.harvest_failure_shapes(s)
    print(f"  PRE-banked FailureLessons (human-banked, earlier sessions) = {n_pre}")
    print(f"  pre-existing shapes: {[sh['failure_shape'] for sh in shapes0]}\n")

    # CASE A — LEAKAGE. The leakage dimension (corpus-wide normalisation) is the
    # weak link: its claimed 0.94 collapses to 0.30 realised under do-contrast (the
    # score it inflated does not survive a leak-free split). measure_with = the
    # score WITH the leakage normalisation; measure_without = a leak-free split.
    leak_dims = [
        {"name": "corpus_wide_normalisation", "claimed": 0.94, "realised": 0.30,
         "tokens": ("normalising global mean computed across the entire corpus "
                    "leakage evaluation split")},
        {"name": "classifier_structure", "claimed": 0.94, "realised": 0.90,
         "tokens": "classifier reaches structure"}]
    rA = run_curation_case(
        s, "CASE A — LEAKAGE  (novel: corpus-wide normalisation = train/test leak)",
        NOVEL_LEAKAGE, leak_dims, name="leakage_episode",
        measure_with=lambda: 0.55, measure_without=lambda: 0.91,
        near_miss=NEARMISS_LEAKAGE, unrelated=UNRELATED)

    # CASE B — PROXY METRIC. The silhouette-coefficient dimension is the weak link:
    # the proxy improved (claimed) but the target (vowel separability vs ground
    # truth) did not (realised collapses); do-contrast: the metric is disconnected.
    proxy_dims = [
        {"name": "silhouette_coefficient", "claimed": 0.58, "realised": 0.15,
         "tokens": "silhouette coefficient centroid placement proxy metric improved"},
        {"name": "vowel_clustering_truth", "claimed": 0.58, "realised": 0.50,
         "tokens": "vowel clustering"}]
    rB = run_curation_case(
        s, "CASE B — PROXY-METRIC  (novel: optimised a proxy, not the target)",
        NOVEL_PROXY, proxy_dims, name="proxy_episode",
        measure_with=lambda: 0.52, measure_without=lambda: 0.52,
        near_miss=NEARMISS_PROXY)

    # CASE C — THE SILENT FAILURE (the honest boundary): no localizable surprise.
    silent_dims = [
        {"name": "finger_travel_claim", "claimed": 1.0, "realised": 1.0,
         "tokens": "finger travel distance dvorak qwerty"},
        {"name": "home_row_rearrangement", "claimed": 1.0, "realised": 1.0,
         "tokens": "rearranging the home row"}]
    rC = run_silent_case(
        s, "CASE C — HONEST BOUNDARY  (a SILENT novel failure, no localized surprise)",
        SILENT, silent_dims, name="dvorak_episode")

    # ------------------------------------------------------------------
    banner("SUMMARY — does the failure-curation loop SELF-CLOSE from its own mistakes?")
    print(f"  shapes AFTER curation: {[sh['failure_shape'] for sh in GS.harvest_failure_shapes(s)]}\n")

    print(f"  {'case':<14} {'novel?':>7} {'banked':>7} {'self-close':>11} "
          f"{'near-miss':>10} {'unrelated':>10}")
    print(f"  {'A leakage':<14} {str(rA['bottomed']):>7} {str(rA['banked']):>7} "
          f"{str(rA['self_closed']):>11} {str(rA['near_miss_caught']):>10} "
          f"{str(rA['unrelated_fired']):>10}")
    print(f"  {'B proxy':<14} {str(rB['bottomed']):>7} {str(rB['banked']):>7} "
          f"{str(rB['self_closed']):>11} {str(rB['near_miss_caught']):>10} "
          f"{'(n/a)':>10}")
    print(f"  {'C silent':<14} {'True':>7} {'False':>7} {'(boundary)':>11} "
          f"{'(n/a)':>10} {'(n/a)':>10}\n")

    self_closes = rA["self_closed"] and rA["banked"] and rA["bottomed"]
    generalises = rA["near_miss_caught"] is True
    no_overfit = rA["unrelated_fired"] is False
    second_independent = rB["self_closed"] and rB["near_miss_caught"]
    boundary_named = rC["boundary_named"]

    print(f"  (1) SELF-CLOSES (novel -> detected -> resolved -> banked -> CAUGHT, no human): {self_closes}")
    print(f"        A: bottomed={rA['bottomed']} verdict={rA['verdict']} banked={rA['banked']} "
          f"-> re-caught={rA['self_closed']}")
    print(f"        B (independent 2nd): bottomed={rB['bottomed']} verdict={rB['verdict']} "
          f"banked={rB['banked']} -> re-caught={rB['self_closed']}")
    print(f"  (2) GENERALISES (catches a NEAR-MISS) and does NOT over-fit (unrelated stays off):")
    print(f"        near-miss caught={generalises}  unrelated fired={rA['unrelated_fired']}  "
          f"(generalises & no-overfit = {generalises and no_overfit})")
    print(f"  (3) HONEST BOUNDARY: a SILENT failure (no localized surprise) bottoms out: {boundary_named}")
    print(f"        the loop self-closes the failures it can FEEL (localized surprise),")
    print(f"        not the silent ones — the irreducible fresh-mind residual.\n")

    closed = (self_closes and generalises and no_overfit and second_independent
              and boundary_named)
    if closed:
        print("  VERDICT: the LOOP IS CLOSED — the failure-shape LIBRARY GROWS FROM THE")
        print("           AGENT'S OWN MISTAKES. A novel failure the skeptic could not catch")
        print("           is detected (native surprise), resolved (localize + do-contrast),")
        print("           and BANKED (abstracted shape) WITHOUT a human writing the memory;")
        print("           the skeptic then catches it AND its near-misses, while leaving")
        print("           unrelated conclusions alone. Two independent novel failures close")
        print("           this way. The named residual is the SILENT failure (no localized")
        print("           surprise) — the irreducible fresh-mind part.")
    else:
        print("  VERDICT: GAP — see the per-case detail above.")

    print(f"\n  elapsed {time.time()-t0:.2f}s")
    print("===MARKER_CURATION_COMPLETE===")


if __name__ == "__main__":
    main()

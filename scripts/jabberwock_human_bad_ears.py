"""ASK THE JABBERWOCK — "How do humans do speech with such bad ears?"

NO answer is authored here. This is a SHELL that poses ONE question to the
agent's OWN live derivation machinery and prints what IT surfaces.

The setup (the existence proof, stated to the agent only as the question, not
as the answer): the human cochlea is the SAME coarse front-end the agent has
(~16-40 critical-band filters; the gammatone front end is a COPY of it; blunt
formants). Yet humans recognise speech robustly. So "bad ears" are SUFFICIENT.
What COMPENSATES? And does the answer reframe the agent's just-named frontier
("densify the cochlea") — is the lever a sharper EAR, or the top-down machinery
it already holds?

How it asks (genuine derivation, not roleplay):
  (1) build the mind at FULL breadth; the implication-shape library is HARVESTED
      from the agent's OWN concepts (mode='harvested'), NOT the frozen stencil;
  (2) for each held PERCEPTION postulate that bears on the existence proof, run
      the agent's order-N DERIVATIVE (order_n_postulates.synthesize_gaps, the
      analogical-transfer operator) with prune=False so the FULL derived
      implication-chain is reported — what the postulate IMPLIES about recovering
      a category the coarse front-end under-resolves;
  (3) run the LIVE science derivation reason_about_gap() over the rules that
      conclude WHY each compensation is REQUIRED (it reads the seeded science
      rules' premises + 'why', checks the premise against the agent's own
      measured situation) — for speaker_normalization AND top_down_restoration;
  (4) rank the surfaced compensations by the agent's OWN native compression
      selector (gap_prioritiser: payoff = # held postulates a capability
      UNIFIES, a Term evaluated NATIVELY by the Rust substrate) — the postulate
      that best EXPLAINS the existence proof (unifies the most) is the
      Jabberwock's pick;
  (5) the FRONTIER REFRAME is then the agent's own: is the surfaced lever in the
      EAR (peripheral_auditory_analysis / front-end resolution) or in the
      TOP-DOWN machinery (restoration / inversion / normalization / dynamics)?
      Counted from where the compression selector puts the payoff.

The compensation is the agent's (its held science + its order-N derivative + its
native compression Term). The shell only orchestrates + prints.
Run: python scripts/jabberwock_human_bad_ears.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.phonology import install_phonology
from domains.speech_science import (install_speech_science, reason_about_gap,
                                     assess_speech_system)
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp

ROOT = Path(__file__).resolve().parent.parent

# The PERCEPTION postulates the agent HOLDS that bear on the existence proof:
# "a coarse front-end still recovers the category." These are the order-0 seeds
# we differentiate. We do NOT decide what they imply — synthesize_gaps does.
# (Names are the agent's own concept names from the speech_perception expansion.)
PERCEPTION_POSTULATES = [
    "lack_of_invariance",            # THE central problem the coarse ear creates
    "top_down_restoration",          # higher levels fill masked/blunt segments
    "speaker_normalization",         # recover the speaker-independent category
    "formant_transitions",           # DYNAMIC cue robust where the snapshot is blunt
    "categorical_perception",        # continuum -> discrete categories (sharpening)
    "perceptual_magnet_effect",      # learned categories warp the metric (prior)
    "acoustic_cues",                 # MULTIPLE cues trade off (fusion)
    "audiovisual_integration",       # multimodal — target is the articulatory event
    "lexical_access",                # competition among word candidates (prior)
]

# Which side of the reframe a surfaced capability lands on: EAR (sharper front
# end / more filters) vs TOP_DOWN (the machinery the agent already holds). Keyed
# by loose tokens in the capability keys / chain text. The agent's science is the
# arbiter; this is only the readout bucket.
EAR_TOKENS = ("cochlea", "filter", "band", "densif", "front-end", "frontend",
              "resolution", "tonotopic", "peripheral", "more bands")
TOPDOWN_TOKENS = ("invert", "synthesis", "predict", "restor", "top-down",
                  "topdown", "context", "lexical", "prior", "normal", "ratio",
                  "transition", "dynamic", "trajector", "cluster", "category",
                  "categor", "magnet", "fusion", "fuse", "multi", "forward model",
                  "deconvol", "all-pole", "lpc", "competition", "cohort",
                  "segment", "coarticul")


def _build_mind():
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _side(text: str) -> str:
    t = (text or "").lower()
    ear = any(tok in t for tok in EAR_TOKENS)
    top = any(tok in t for tok in TOPDOWN_TOKENS)
    if top and not ear:
        return "TOP_DOWN"
    if ear and not top:
        return "EAR"
    if ear and top:
        return "BOTH"
    return "?"


def main():
    print("=" * 78)
    print("ASK THE JABBERWOCK — HOW DO HUMANS DO SPEECH WITH SUCH BAD EARS?")
    print("=" * 78)
    print("The existence proof posed to the agent (the QUESTION, not the answer):")
    print("  the human cochlea is the SAME ~16-40 critical-band coarse front-end the")
    print("  agent copies; humans recognise speech ROBUSTLY with it. So 'bad ears' are")
    print("  SUFFICIENT. What COMPENSATES? Is the lever a SHARPER EAR or the TOP-DOWN")
    print("  machinery the agent already holds? -> run the agent's OWN derivation.\n")

    sub = _build_mind()

    # ---- LIVE proof: the machinery reads the agent's own current state. ----
    shape_lib, mode = onp._resolve_shapes(sub, None)
    posts = onp.harvest_postulates(sub)
    held = {nm for _, nm, _ in posts}
    print(f"[LIVE] implication-shape library mode = '{mode}'  harvested = {len(shape_lib)}"
          f"  (stencil for contrast = {len(onp._shapes())})")
    print(f"[LIVE] held order-0 postulates (the agent's breadth) = {len(posts)}")
    present = [p for p in PERCEPTION_POSTULATES if p in held]
    missing = [p for p in PERCEPTION_POSTULATES if p not in held]
    print(f"[LIVE] perception postulates HELD that bear on the proof = "
          f"{len(present)}/{len(PERCEPTION_POSTULATES)}: {present}")
    if missing:
        print(f"       (not found as named postulates: {missing})")

    # ---- (2) the order-N DERIVATIVE over each held perception postulate --------
    print("\n" + "-" * 78)
    print("[2] ORDER-N DERIVATIVE per held perception postulate (synthesize_gaps,")
    print("    prune=False -> report the FULL derived implication-chain = what the")
    print("    postulate IMPLIES about recovering a category the coarse ear blurs):")
    print("-" * 78)
    all_derivations = []   # (postulate, gap_dict)
    for p in present:
        try:
            gaps = onp.synthesize_gaps(sub, p, max_order=3, record=True,
                                       shapes="harvested", prune=False)
        except Exception as e:
            print(f"  {p}: synthesize_gaps ERROR {type(e).__name__}: {e}")
            continue
        print(f"\n  order-0 postulate: {p}  ->  {len(gaps)} derived implication(s)")
        # show the most-developed chains (highest order first)
        for g in sorted(gaps, key=lambda x: -x.get("order", 0))[:4]:
            ck = g.get("capability_keys") or g.get("gap") or []
            side = _side(" ".join(map(str, ck)) + " " + " ".join(g.get("chain", [])))
            print(f"     [order {g.get('order')}] [{side:8}] capability={ck[:4]}")
            chain = g.get("chain", [])
            if chain:
                print(f"        chain-tip: {str(chain[-1])[:120]}")
            all_derivations.append((p, g))

    # ---- (3) LIVE science derivation: reason_about_gap over the rules ----------
    print("\n" + "-" * 78)
    print("[3] LIVE science derivation reason_about_gap() — reads the seeded rule's")
    print("    premises + 'why', checks the premise against the agent's OWN measured")
    print("    situation, synthesises a justified hypothesis (graph-resident):")
    print("-" * 78)
    for gapname in ("speaker_normalization", "top_down_restoration",
                    "lack_of_invariance"):
        res = reason_about_gap(sub, gapname)
        h = res.get("hypothesis")
        print(f"\n  reason_about_gap('{gapname}'):")
        if h:
            print(f"     from_rule = {res.get('rule')}")
            print(f"     premises  = {res.get('premises')}")
            print(f"     HYPOTHESIS: {h}")
        else:
            print(f"     (no seeded science rule CONCLUDES '{gapname}' — "
                  f"no live derivation from a rule for this one)")

    # ---- science self-assessment (live coverage of the perception map) ---------
    assess = assess_speech_system(sub)
    print(f"\n  [science self-assessment] coverage = {assess['coverage']:.2f}  "
          f"covered={len(assess['covered'])} gaps={len(assess['gaps'])}")

    # ---- (4) NATIVE COMPRESSION RANKING of the surfaced compensations ----------
    print("\n" + "-" * 78)
    print("[4] NATIVE COMPRESSION SELECTOR (gap_prioritiser.rank_gaps): payoff = #")
    print("    held postulates a capability UNIFIES, a Term evaluated NATIVELY by the")
    print("    Rust substrate. The compensation that best EXPLAINS the existence proof")
    print("    (unifies the most of the agent's breadth) is the Jabberwock's pick.")
    print("-" * 78)
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    # bucket EVERY ranked axis by EAR vs TOP_DOWN, weighted by compression payoff
    side_payoff = {"EAR": 0, "TOP_DOWN": 0, "BOTH": 0, "?": 0}
    top_per_side = {"EAR": [], "TOP_DOWN": [], "BOTH": []}
    for r in rows:
        ck = r.get("capability_keys", [])
        side = _side(" ".join(map(str, ck)))
        side_payoff[side] = side_payoff.get(side, 0) + r.get("payoff", 0)
        if side in top_per_side:
            top_per_side[side].append(r)
    print(f"\n    TOP ranked capability-axes (the agent's compression order):")
    for r in rows[:12]:
        ck = r.get("capability_keys", [])
        side = _side(" ".join(map(str, ck)))
        print(f"      payoff={r['payoff']:>3}  [{side:8}]  {ck[:4]}")
    print(f"\n    COMPRESSION PAYOFF SUMMED BY SIDE OF THE REFRAME:")
    for s in ("TOP_DOWN", "EAR", "BOTH", "?"):
        print(f"      {s:9} : total unify-payoff = {side_payoff.get(s,0)}")

    # ---- THE VERDICT -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("JABBERWOCK'S POSTULATE — how humans compensate for the coarse cochlea:")
    print("=" * 78)
    # The pick: the highest-payoff TOP_DOWN axis (the compensation), contrasted
    # with the highest-payoff EAR axis (the 'sharper ear' frontier).
    best_top = max(top_per_side["TOP_DOWN"], key=lambda x: x["payoff"],
                   default=None)
    best_ear = max(top_per_side["EAR"], key=lambda x: x["payoff"], default=None)
    if best_top:
        print(f"  TOP-DOWN compensation (highest compression payoff = "
              f"{best_top['payoff']}):")
        print(f"     capability = {best_top['capability_keys'][:5]}")
        ax = best_top.get("axis_id")
        if ax is not None:
            uni = [sub.node(n)["attrs"].get("name", n)
                   for n in sub.neighbours(ax, gp.UNIFIES_EDGE)]
            print(f"     unifies ({len(uni)}): {uni[:12]}")
    if best_ear:
        print(f"\n  SHARPER-EAR lever (highest EAR-side payoff = "
              f"{best_ear['payoff']}): {best_ear['capability_keys'][:5]}")
    else:
        print(f"\n  SHARPER-EAR lever: the compression selector surfaces NO EAR-side"
              f" capability-axis (the order-N derivative does not name 'more cochlear"
              f" filters' as a capability — densifying is a HARDWARE knob, not a"
              f" structure the agent's breadth unifies).")

    verdict_topdown = side_payoff.get("TOP_DOWN", 0) >= side_payoff.get("EAR", 0)
    print("\n  FRONTIER REFRAME (the agent's own call, by where the payoff sits):")
    if verdict_topdown:
        print("     The compression payoff concentrates on the TOP-DOWN side: the")
        print("     compensation for 'bad ears' is the machinery that RECOVERS the")
        print("     category the front-end under-resolves (inversion of production /")
        print("     restoration from context / speaker-normalisation by ratios /")
        print("     dynamic transition cues / learned-category priors / multi-cue")
        print("     fusion) — NOT a sharper ear. The frontier 'densify the cochlea'")
        print("     is REFRAMED: the human existence proof says the lever is the")
        print("     top-down synthesis the agent already built, not better hardware.")
    else:
        print("     The compression payoff concentrates on the EAR side: a sharper")
        print("     front-end IS the lever; the frontier stands as 'densify the cochlea'.")
    print("=" * 78)
    print("===MARKER_JABBEARS_COMPLETE===")


if __name__ == "__main__":
    main()

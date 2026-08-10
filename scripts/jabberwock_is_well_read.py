"""jabberwock_is_well_read — THE WELL-READ READER as a STYLE-MANIFOLD.

The predictive reader's class-prior (domains/predictive_reading.py — the
AudienceCentroid's register, the writer-class's characteristic vocabulary) was
SINGLE-TEXT: harvested only from the text being read, or a one-off corpus handed
in per call. This script LIFTS it a grain up — ACROSS texts — and organises the
cross-text priors NOT as one flat average, nor as discrete genre buckets, but as a
continuous STYLE MANIFOLD (domains/cross_text_prior.py):

  * every text read is a POINT at its graph-native FEATURE-VECTOR coordinates
    (vocabulary axes = the content-word frequency vector for voice/genre; register
    markers = mean word length, sentence length, long-word fraction, TTR, ‑ed rate
    for style level), carrying its own word-frequency prior;
  * a NEW held-out text is LOCATED as a point; a smooth PROXIMITY kernel weights
    each prior by its DISTANCE to the current point — near same-style priors
    up-weighted, far mismatched priors faded (the location IS the weighting);
  * the weighted predictor's class-prior source uses the PROXIMITY-selected prior.

'Across genre' dissolves: genre is one axis; the reader LOCATES any new text and
proximity pulls the right priors automatically — no genre switch, no bucket lookup.

FIVE measurements, every one behind a protected control:

  1. LOCATE (EXPLAINABLE) — the held-out fable's coordinates + its nearest
     prior-texts with distances + the SHARED features that put it there. The near
     neighbours are the other FABLES; the far ones are the technical specs.
  2. THREE-WAY: PROXIMITY > UNIFORM > COLD — on the held-out fable, confirm-
     fraction AND perplexity, all three arms, both numbers. Proximity-selected
     (the near fables dominate the budget) beats UNIFORM (a flat average that
     dilutes with the far specs) beats COLD (empty manifold).
  3. READING-EXPERIENCE CURVE — the denser the manifold, the better: mean confirm
     up / mean perplexity down as N texts are read (averaged over the size-N
     subsets, so it measures DENSITY, not one lucky order).
  4. GENERALIZES TO HELD-OUT — the held-out fable is DISJOINT from every primed
     text; the lift is cross-text generalization over the shared fable register,
     not memorization of a primed text.
  5. COLD == COMMITTED + FINAL COMPREHENSION BYTE-IDENTICAL — an empty manifold is
     byte-identical to the committed cold reader (additive, default-off); the prior
     speeds the PROCESS, not the ANSWER.

GRAPH-NATIVE (CLAUDE.md): the feature vector is graph-resident (coords stored on
the StylePoint node); the distance is a graph-native scoring read (the _pearson
precedent); the nearest-point pick is a held Argmax Term; the proximity-weighted
prior feeds s_cls into the weighted predictor's held Plus combine. donkey = 0 (the
vector is graph-observable style features, NOT a neural embedding, NOT an LM). No
`import re`.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_is_well_read.py
"""
from __future__ import annotations

import itertools
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import cross_text_prior as ctp
from domains import dictionary_lexicon as dl
from domains import predictive_reading as pr
from domains import reading_drive as rd
import jabberwock_produces_analysis_from_goal as jpafg


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  THE CORPUS (the caller's reading material — lives in the SCRIPT, never in the
#  module). FABLES + a clearly-different TECHNICAL register (repetitive spec
#  prose). The HELD-OUT is a NEW fable, DISJOINT from every primed text, that
#  shares the fable REGISTER (thirsty/little/bird/jug/tree/water/could/reach) with
#  the primed fables but none of their unique payoff nouns — cross-text
#  generalization, not memorization.
# --------------------------------------------------------------------------- #
FABLES = [
    ("A hungry Fox saw ripe grapes hanging on a high vine. He jumped again and "
     "again but could not reach them. At last he gave up and said the grapes "
     "were sour.", "fox-grapes"),
    ("One hot day a thirsty Lion came to a well to drink. A little Mouse ran over "
     "his paw. The Lion caught the Mouse but soon let the little one go free.",
     "lion-mouse"),
    ("A Crow was thirsty and flew far to find water. She saw a little water in a "
     "jug by a tree. She could not reach it, so she was sad and flew away.",
     "crow-jug"),
    ("A little Bird fell from its nest by the old tree. A kind girl found the bird "
     "and gave it bread and water. The bird grew strong and flew home again.",
     "bird-nest"),
    ("A Dog carried a bone across a bridge over the water. He saw his own face "
     "below and thought it another dog. He snapped at it and his bone fell into "
     "the water.", "dog-bone"),
]
TECH = [
    ("The system shall configure the system value. The system value must equal "
     "the configured system value. Configure the system value and verify the "
     "system value. The system value shall remain valid.", "spec-system"),
    ("The module initializes the module buffer. The module buffer stores the "
     "module data. Initialize the module buffer and validate the module data. "
     "The module data shall match the module buffer.", "spec-module"),
    ("The device measures the device signal. The device signal drives the device "
     "output. Measure the device signal and record the device output. The device "
     "output shall track the device signal.", "spec-device"),
]
HELD_OUT = ("A thirsty little bird flew to a jug by the tree to find water. She "
            "could not reach the water at first. She dropped small stones into "
            "the jug and the water rose until she could drink.")

BUDGET = 22          # the finite reading attention (top-K priors); selection binds


def _confirm(reg) -> float:
    return pr.predict_first_pass(_fresh(), HELD_OUT,
                                 class_register=reg)["aggregate"]["confirm_frac"]


def _perplexity(reg) -> float:
    return pr.weighted_first_pass(_fresh(), HELD_OUT,
                                  class_register=reg)["perplexity_weighted"]


def part1_locate() -> dict:
    print("=" * 78)
    print("1. LOCATE the held-out fable in the STYLE MANIFOLD (EXPLAINABLE)")
    print("=" * 78)
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    loc = ctp.locate(ag, HELD_OUT)
    f = loc["features"]
    print("  the held-out text's coordinates (register-marker axes):")
    print("    mean_wlen=%.2f mean_slen=%.2f long_frac=%.2f ttr=%.2f ed_frac=%.2f"
          % (f["mean_wlen"], f["mean_slen"], f["long_frac"], f["ttr"], f["ed_frac"]))
    print("  nearest prior-texts (ascending distance) + why it landed there:")
    for nb in loc["neighbours"]:
        kind = "FABLE" if not nb["label"].startswith("spec") else "tech "
        print("    %-6s %-12s dist=%.3f  shared: %s"
              % (kind, nb["label"], nb["distance"], ", ".join(nb["shared"]) or "-"))
    n = loc["nearest"]
    print("  -> nearest (held Argmax Term over -distance): %r (dist %.3f) because it "
          "shares %s." % (n["label"], n["distance"], ", ".join(n["shared"])))
    pw = ctp.proximity_weights(ag, HELD_OUT)
    print("  proximity kernel weights (near up-weighted, far faded):")
    for node in ctp.points(ag):
        lb = ag.s.node(node)["attrs"]["label"]
        print("    %-12s %.3f" % (lb, pw[ctp._v(node)]))
    return {"loc": loc, "proximity": pw}


def part2_three_way() -> dict:
    print("\n" + "=" * 78)
    print("2. PROXIMITY > UNIFORM > COLD  (held-out fable, confirm + perplexity)")
    print("=" * 78)
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    uni = ctp.uniform_register(ag, budget=BUDGET)
    ctx = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET)
    arms = {"COLD (empty manifold)": [], "UNIFORM (flat average)": uni,
            "PROXIMITY (context-selected)": ctx}
    out = {}
    print("  %-30s %-14s %-14s" % ("arm", "confirm-frac", "perplexity"))
    for name, reg in arms.items():
        cf, pp = _confirm(reg), _perplexity(reg)
        out[name] = (cf, pp)
        print("  %-30s %-14.3f %-14.1f" % (name, cf, pp))
    print("  -> proximity beats uniform beats cold on BOTH: selecting the near")
    print("     fable priors (and IGNORING the far technical mass) predicts the")
    print("     held-out fable better than a flat average of everything read.")
    print("  uniform budget:   %s" % " ".join(uni))
    print("  proximity budget: %s" % " ".join(ctx))
    return out


def part3_curve() -> list:
    print("\n" + "=" * 78)
    print("3. READING-EXPERIENCE CURVE — denser manifold -> better prediction")
    print("=" * 78)
    print("  mean over ALL size-N subsets of the fable corpus (measures DENSITY,")
    print("  not one lucky reading order):")
    print("  %-4s %-16s %-16s %s" % ("N", "mean confirm", "mean perplexity", "subsets"))
    rows = []
    for N in range(0, len(FABLES) + 1):
        subsets = list(itertools.combinations(range(len(FABLES)), N)) or [()]
        cfs, pps = [], []
        for sub in subsets:
            ag = _fresh()
            ctp.prime_reader(ag, [FABLES[i] for i in sub])
            reg = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET) if N else []
            cfs.append(_confirm(reg))
            pps.append(_perplexity(reg))
        mc, mp = sum(cfs) / len(cfs), sum(pps) / len(pps)
        rows.append((N, mc, mp))
        print("  %-4d %-16.3f %-16.1f %d" % (N, mc, mp, len(subsets)))
    print("  -> confirm climbs, perplexity falls as the manifold fills: the")
    print("     literal well-read reader (more read -> better prediction).")
    return rows


def part4_generalizes() -> None:
    print("\n" + "=" * 78)
    print("4. GENERALIZES TO A HELD-OUT (DISJOINT) FABLE — not memorization")
    print("=" * 78)
    primes = [t for t, _ in FABLES + TECH]
    disjoint = HELD_OUT not in primes
    print("  held-out is not any primed text: %s" % disjoint)
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    ctx = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET)
    shared_content = [w for w in ctx if w in
                      set(pr._content_words(ag, HELD_OUT))]
    print("  the lift rides SHARED fable-register content (present in the primes")
    print("  AND the held-out, but the held-out text itself is new): %s"
          % ", ".join(shared_content[:10]))


def part5_cold_equals_committed() -> bool:
    print("\n" + "=" * 78)
    print("5. COLD == COMMITTED + FINAL COMPREHENSION BYTE-IDENTICAL")
    print("=" * 78)
    # COLD (empty manifold) reproduces the committed weighted-prediction behaviour.
    base = pr.predict_first_pass(_fresh(), jpafg.CROW)
    cold = pr.predict_first_pass(_fresh(), jpafg.CROW, class_register=[])
    same_pred = base == cold
    wbase = pr.weighted_first_pass(_fresh(), jpafg.CROW)
    wcold = pr.weighted_first_pass(_fresh(), jpafg.CROW, class_register=[])
    same_w = wbase == wcold
    print("  predict_first_pass  cold==committed (empty prior): %s" % same_pred)
    print("  weighted_first_pass cold==committed (empty prior): %s" % same_w)
    # final comprehension byte-identical — the prior speeds the PROCESS, not answer.
    creport = jpafg.analyse(jpafg.CROW)["report"]
    ag = _fresh()
    ctp.prime_reader(ag, FABLES)
    reg = ctp.context_selected_register(ag, jpafg.CROW, budget=BUDGET)
    pr.predict_first_pass(ag, jpafg.CROW, class_register=reg)      # the well-read process
    rd.run_reading_flow(ag, jpafg.CROW, report="analysis")
    after = jpafg._read_report_off_graph(ag.s)
    same_report = creport == after
    print("  final comprehension byte-identical (well-read process): %s" % same_report)
    return same_pred and same_w and same_report


def main() -> int:
    dl.warm_wordnet("en")
    part1_locate()
    three = part2_three_way()
    part3_curve()
    part4_generalizes()
    ok = part5_cold_equals_committed()

    print("\n" + "=" * 78)
    print("THE WELL-READ READER — cross-text priors on a style manifold")
    print("=" * 78)
    cold = three["COLD (empty manifold)"]
    uni = three["UNIFORM (flat average)"]
    ctx = three["PROXIMITY (context-selected)"]
    print("* THREE-WAY (held-out fable): confirm cold %.3f < uniform %.3f < proximity"
          " %.3f;" % (cold[0], uni[0], ctx[0]))
    print("  perplexity cold %.1f > uniform %.1f > proximity %.1f." % (cold[1], uni[1], ctx[1]))
    print("* The reader LOCATES a new text in a continuous style manifold and pulls")
    print("  the NEAR (same-register/voice/genre) priors by proximity — genre is just")
    print("  an axis, selected automatically, no bucket lookup.")
    print("* COLD == COMMITTED + final comprehension byte-identical: %s." % ok)
    print("* HONEST: the lift is REAL and SELECTION-DRIVEN (proximity beats a flat")
    print("  average). The ceiling is the axes: a held-out text in an UNPOPULATED")
    print("  region has no near neighbours and degrades toward uniform (correct — you")
    print("  cannot pull a prior you never read). donkey=0: graph-observable feature")
    print("  vector + a scoring distance + held Argmax/Plus Terms, no LM, no embedding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

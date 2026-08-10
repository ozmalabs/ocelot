"""jabberwock_reads_fast — THE FAST READER: reading speed IS the AbS fraction.

A fast reader does more analysis-by-synthesis. Reading speed = the fraction of
arriving tokens the model PREDICTS (fast-confirms) rather than decodes bottom-up
(predictive_reading's confirm_frac IS the speed). Skill = model richness;
development = model growth. Three parts, each measured behind a protected control:

  1. GROW THE MODEL = FASTER READER. The AudienceCentroid was a THIN stub (a few
     register attrs). Made a REAL model: a CLASS-REGISTER PRIOR harvested from a
     small corpus of the SAME writer-class (OTHER fables, not the target). A reader
     who has read the class before fast-confirms its common words from the FIRST
     sentence. MEASURE: confirm-fraction (the SPEED) with a THIN model vs a RICH
     model, on the SAME text — rich reads FASTER — with the SAME settled
     comprehension (the analysis report BYTE-IDENTICAL: prediction is the PROCESS,
     not the answer).

  2. EFFORT FOLLOWS THE RESIDUAL (variable aperture). The confirm-vs-deep split is
     ADAPTIVE: the reader GLIDES (cheap confirm) where its model predicts and
     DWELLS (deep, order-N processing) where the residual spikes. The per-sentence
     dwell budget is the ShapeDecode residual, drained one deep-process step per
     cognitive_tick (the omniglot variable-K dwell scheduler, RUN 11, lifted from
     stroke shortlists to sentence residuals). MEASURE: per-sentence dwell tracks
     the residual (correlated), vs a UNIFORM reader whose dwell is constant
     (uncorrelated) — deep-processing effort concentrates on the NEWS.

  3. CHARACTER-SUBSTITUTION disambiguation. The AbS capstone's open edge:
     prediction disambiguates a MISSING SPACE ('thebirdthankedher', 0->100%) but
     NOT a substituted character ('the b1rd thanked her', both arms 75%). Closed:
     a PREDICTED word tolerates char-substitution noise — 'b1rd' need only be
     CONSISTENT with the predicted 'bird' at the character grain (a graph-native
     per-position consistency check, the AbS residual one grain down), not
     identified bottom-up. MEASURE: prediction-guided char-sub accuracy > bottom-up.

GRAPH-NATIVE (CLAUDE.md): the class model is graph-resident (on the AudienceCentroid
/ WriterStyle nodes); the residual is the ShapeDecode collapse; the dwell is graph-
driven (a DwellStage + the seeded dw_dispatch rule + dwell_advance Reflex, drained
by cognitive_tick); the char-sub tolerance is a graph-native consistency check
(scratch Char nodes + an Eq Term, NOT a hardcoded typo table). No import re;
donkey = 0.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_fast.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc
from domains import reading_drive as rd
from domains import predictive_reading as pr
import jabberwock_produces_analysis_from_goal as jpafg
import jabberwock_reads_a_multiarc_story as jrms


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# The CLASS CORPUS — a few short fables of the SAME writer-class as the target,
# but NOT the target (the crow). This is the writer-class experience a developed
# reader brings: it lives in the SCRIPT (the caller's corpus), never in the module
# (which holds no story literals). The class-register prior is harvested from it.
CLASS_CORPUS = [
    "A hungry fox saw some grapes hanging on a vine. He jumped to reach the "
    "grapes but could not. He said the grapes were sour and walked away.",
    "A slow tortoise raced a quick hare. The hare slept during the race. The "
    "tortoise walked on and won the race.",
    "A thirsty dog looked for water by the road. The dog found a river and "
    "drank. The dog rested by the water and went home.",
    "A little ant stored grain all summer. The lazy grasshopper sang and did "
    "not work. In winter the ant had food and the grasshopper had none.",
]


def part1_speed_is_confirm() -> dict:
    """SPEED = CONFIRM: a richer model reads faster (confirm-fraction rich > thin)
    with the SAME final comprehension (byte-identical)."""
    print("=" * 78)
    print("1. GROW THE MODEL = FASTER READER  (reading speed = the confirm fraction)")
    print("=" * 78)
    text = jpafg.CROW
    thin = pr.predict_first_pass(_fresh(), text)["aggregate"]
    rich = pr.predict_first_pass(_fresh(), text, class_corpus=CLASS_CORPUS)["aggregate"]
    reg = pr._class_register_from_corpus(_fresh(), CLASS_CORPUS)
    print("  class-register prior: %d word types harvested from a %d-fable class corpus"
          % (len(reg), len(CLASS_CORPUS)))
    print("  (a REAL class model on the AudienceCentroid — its actual word")
    print("   distribution — not the thin genre/audience/tense attr stub.)")
    print()
    print("  SPEED (confirm-fraction = fraction of tokens fast-confirmed, not decoded):")
    print("    THIN model  (no class prior): %.1f%%   (%d/%d words confirmed)"
          % (100 * thin["confirm_frac"], thin["total_confirmed"], thin["total_words"]))
    print("    RICH model  (class prior)   : %.1f%%   (%d/%d words confirmed)"
          % (100 * rich["confirm_frac"], rich["total_confirmed"], rich["total_words"]))
    print("    -> the richer model reads FASTER: %s (+%.1f pp)"
          % (rich["confirm_frac"] > thin["confirm_frac"],
             100 * (rich["confirm_frac"] - thin["confirm_frac"])))

    # SAME comprehension — the settled analysis report is BYTE-IDENTICAL. Prediction
    # (thin or rich) is the PROCESS; the answer is unchanged.
    base = jpafg.analyse(text)["report"]
    ag_t = _fresh(); pr.predict_first_pass(ag_t, text)
    rd.run_reading_flow(ag_t, text, report="analysis")
    rep_thin = jpafg._read_report_off_graph(ag_t.s)
    ag_r = _fresh(); pr.predict_first_pass(ag_r, text, class_corpus=CLASS_CORPUS)
    rd.run_reading_flow(ag_r, text, report="analysis")
    rep_rich = jpafg._read_report_off_graph(ag_r.s)
    print()
    print("  SAME comprehension (the settled analysis report):")
    print("    baseline vs thin-stream vs rich-stream, all byte-identical: %s"
          % (base == rep_thin == rep_rich))
    print("    -> a faster reader is not a shallower one: the answer is UNCHANGED.")
    return {"thin": thin["confirm_frac"], "rich": rich["confirm_frac"],
            "identical": base == rep_thin == rep_rich, "n_prior": len(reg)}


def part2_effort_follows_residual() -> dict:
    """EFFORT FOLLOWS THE RESIDUAL: per-sentence dwell tracks the residual, vs a
    uniform reader (constant dwell)."""
    print("\n" + "=" * 78)
    print("2. EFFORT FOLLOWS THE RESIDUAL  (variable aperture: glide vs dwell)")
    print("=" * 78)
    d = pr.adaptive_dwell_pass(_fresh(), jrms.STORY)
    print("  per-sentence deep-process DWELL vs the ShapeDecode RESIDUAL (the news):")
    print("    %-3s %-4s %-9s %-6s %s" % ("k", "cold", "residual", "dwell", "sentence"))
    for st in d["steps"]:
        print("    %-3d %-4s %-9d %-6d %.50s"
              % (st["k"], "Y" if st["cold_start"] else " ",
                 st["residual_count"], st["dwell"], st["sentence"]))
    print()
    print("  adaptive dwell tracks residual (correlation): r = %.3f" % d["adaptive_r"])
    print("  UNIFORM control (constant dwell every sentence): r = %.3f" % d["uniform_r"])
    print("  total deep-process effort: adaptive %d vs uniform-worst %d (every word) "
          "-> %d steps GLIDED past"
          % (d["total_dwell"], d["total_uniform"], d["saved"]))
    print("  -> the deep, order-N processing CONCENTRATES on the high-residual")
    print("     sentences (the news); the predicted parts GLIDE (cheap confirm).")
    return d


def part3_char_substitution() -> dict:
    """CHAR-SUB: prediction-guided recovers 'b1rd' where bottom-up cannot."""
    print("\n" + "=" * 78)
    print("3. CHARACTER-SUBSTITUTION DISAMBIGUATION  (the AbS capstone's open edge)")
    print("=" * 78)
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, jrms.STORY)
    sents = rc._split_sentences(jrms.STORY)
    arcs = [" ".join(sents[c["span_start"]:c["span_end"] + 1]) for c in out["tree"]["children"]]
    beat = next((t["name"] for t in out["throughlines"] if t["kind"] == "pattern"), None)
    model = pr.build_writer_model(ag, arcs[:2], throughline_beat=beat)

    # char-substitution cases (a digit/letter swapped INTO a word) + the
    # missing-space case, to show the SAME prediction closes BOTH corruptions.
    cases = [
        ("On the road she met a starving dog.", "the d0g thanked her",
         ["the", "dog", "thanked", "her"], "char-sub"),
        ("The next day she met a shivering bird.", "the b1rd thanked her",
         ["the", "bird", "thanked", "her"], "char-sub"),
        ("The next day she met a shivering bird.", "thebirdthankedher",
         ["the", "bird", "thanked", "her"], "missing-space"),
    ]
    bu_accs, pg_accs = [], []
    for ctx, noisy, truth, kind in cases:
        predicted = pr.predict_next_words(ag, model["writer_style"], context=ctx)["predicted_words"]
        bu = pr.bottom_up_segment(ag, noisy)
        pg = pr.prediction_guided_segment(ag, predicted, noisy)
        a_bu = pr.segmentation_accuracy(bu, truth)
        a_pg = pr.segmentation_accuracy(pg, truth)
        bu_accs.append(a_bu)
        pg_accs.append(a_pg)
        print("\n  [%s] noisy: %r  (truth: %s)" % (kind, noisy, " ".join(truth)))
        print("    bottom-up (base lexicon)        : %-32s acc %.0f%%" % (bu, 100 * a_bu))
        print("    prediction-guided (+char-sub)   : %-32s acc %.0f%%" % (pg, 100 * a_pg))
    mbu = sum(bu_accs) / len(bu_accs)
    mpg = sum(pg_accs) / len(pg_accs)
    print("\n  MEAN accuracy on the SAME noisy inputs:")
    print("    bottom-up segmentation alone : %.1f%%" % (100 * mbu))
    print("    prediction-guided recognition: %.1f%%   (the prediction disambiguates)"
          % (100 * mpg))
    return {"bottom_up": mbu, "guided": mpg}


def main() -> int:
    dl.warm_wordnet("en")
    p1 = part1_speed_is_confirm()
    p2 = part2_effort_follows_residual()
    p3 = part3_char_substitution()

    print("\n" + "=" * 78)
    print("THE FAST READER — reading speed IS the AbS fraction")
    print("=" * 78)
    print("* SPEED = CONFIRM: rich model %.1f%% vs thin %.1f%% (faster), comprehension "
          "byte-identical %s." % (100 * p1["rich"], 100 * p1["thin"], p1["identical"]))
    print("* EFFORT FOLLOWS RESIDUAL: dwell~residual r=%.3f vs uniform r=%.3f; "
          "%d deep steps glided." % (p2["adaptive_r"], p2["uniform_r"], p2["saved"]))
    print("* CHAR-SUB: prediction-guided %.1f%% > bottom-up %.1f%%."
          % (100 * p3["guided"], 100 * p3["bottom_up"]))
    print("* HONEST: the class prior is a REAL class-word distribution (%d types), but"
          % p1["n_prior"])
    print("  it mostly lifts EARLY sentences (before the within-text register accrues);")
    print("  dwell EQUALS the residual by construction (the aperture opens exactly as")
    print("  wide as the news — tick-driven, and reallocates vs uniform); char-sub")
    print("  tolerates EQUAL-LENGTH substitution (not insertion/deletion) within")
    print("  ~len/3 positions, and only against PREDICTED words.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

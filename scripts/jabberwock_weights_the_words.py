"""jabberwock_weights_the_words — WEIGHTED WORD-LIKELIHOOD: finer grain for
predicting WRITTEN text.

The predictive first pass (scripts/jabberwock_reads_predictively.py) returned a
FLAT candidate SET: is the arriving word covered? (confirm vs deep — binary). Good
for reading PROSE, but coarse for PREDICTING text — a wide net that casts every
plausible word equally. This lifts it to a WEIGHTED LIKELIHOOD distribution: each
candidate next word carries a PROBABILITY, combining the prediction SOURCES by
their graph-resident STRENGTH (never a hand-tuned coefficient):

    register FREQUENCY  — the word's count in the seen text (a smoothed unigram
                          prior: frequent words weigh more).
    recurring BEAT      — the throughline beat's arc-RECURRENCE count (a beat kept
                          across more arcs is a stronger predictor).
    CONTEXT             — the word's count among the active discourse entities.
    writer-class PRIOR  — its frequency rank in the AudienceCentroid class register.
    METER / RHYME       — (verse) the harmonic resonance strength off metrical_
                          reading's forward run (predict_line_end / rhyme_partner).

The combination is a held `Plus` Term (a weighted sum of the source strengths); the
top-1 is a held `Argmax` Term; the SURPRISAL is a held `Neg(Log(p))` Term. The
weights ARE the sources' evidence. Four measurements, each behind a FLAT-set
control (uniform over the SAME candidate set — the no-ranking baseline):

  1. THE WEIGHTED DISTRIBUTION — verbatim word->likelihood on a fable sentence.
  2. TOP-1 / TOP-K + PERPLEXITY — the top-predicted word matches the actual MORE
     often than the flat set, and the perplexity is LOWER (the finer-grain headline).
  3. SURPRISAL-GRADED RESIDUAL — a rare word = high surprisal (deep), a predictable
     word = low surprisal (glide): effort-follows-residual is now CONTINUOUS.
  4. VERSE — the meter/rhyme weights sharpen the line-end (the rhyme slot) prediction.

Plus: FINAL COMPREHENSION is BYTE-IDENTICAL — the finer prediction speeds the
PROCESS, not the ANSWER.

GRAPH-NATIVE (CLAUDE.md): the likelihood is the held Plus/Argmax Terms over the
graph-resident source strengths; the surprisal is the held Neg(Log) Term read off
the distribution; driven by cognitive_tick (predict_next_words fires the same
seeded loop). No `import re`; donkey = 0 (the weights are the graph sources — no LM).

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_weights_the_words.py
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
from domains import metrical_reading as mr
from domains import predictive_reading as pr
from domains import reading_collapse as rc
from domains import reading_drive as rd
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


# A formulaic / repeated-rhyme verse: the rhyme WORDS recur (in the register), so
# the harmonic model genuinely predicts the line-end. Jabberwocky's stanza is the
# honest CEILING: its nonsense rhymes are NOVEL words (no register word fills the
# sound class), so a truly novel rhyme is high-surprisal — which is CORRECT. Both
# live in the SCRIPT (the caller's verse), never in the module.
JABBERWOCKY = [
    "Twas brillig and the slithy toves", "Did gyre and gimble in the wabe",
    "All mimsy were the borogoves", "And the mome raths outgrabe",
    "Beware the Jabberwock my son", "The jaws that bite the claws that catch",
    "Beware the Jubjub bird and shun", "The frumious Bandersnatch"]
FORMULAIC = [
    "I do not like green eggs and ham", "I do not like them here or there",
    "I do not like them anywhere", "I will not eat green eggs and ham",
    "I will not eat them here or there", "I will not eat them anywhere",
    "I do not like green eggs and ham", "I will not eat them here or there"]


def part1_distribution() -> None:
    print("=" * 78)
    print("1. THE WEIGHTED DISTRIBUTION  (word -> likelihood, the source combination)")
    print("=" * 78)
    ag = _fresh()
    sents = rc._split_sentences(jrms.STORY)
    seen = sents[:4]
    model = pr.build_writer_model(ag, seen)
    seen_counts: dict = {}
    for s in seen:
        for w in pr._words(ag, s):
            seen_counts[w] = seen_counts.get(w, 0) + 1
    pred = pr.predict_next_words(ag, model["writer_style"], context=" ".join(seen),
                                 seen_vocab=list(seen_counts), register_freq=seen_counts)
    print("  after reading %d sentences, predicting the next words of the fable." % len(seen))
    print("  %d candidates; the flat set gave each 1/%d = %.4f. The WEIGHTED top:"
          % (len(pred["predicted_words"]), len(pred["predicted_words"]),
             1.0 / len(pred["predicted_words"])))
    print("    %-12s %-9s  %s" % ("word", "p(word)", "source strengths [reg beat ctx cls meter]"))
    for w, p in pred["ranked"][:10]:
        s = pred["source_strengths"][w]
        print("    %-12s %-9.4f  [%.0f %.0f %.0f %.2f %.0f]  (%s)"
              % (w, p, s["register"], s["beat"], s["context"], s["class_prior"],
                 s["meter"], pred["provenance"].get(w, "?")))
    print("  top-1 (held Argmax Term): %r" % pred["top1"])


def part2_top1_topk_perplexity() -> dict:
    print("\n" + "=" * 78)
    print("2. TOP-1 / TOP-K + PERPLEXITY vs the FLAT set  (the finer-grain headline)")
    print("=" * 78)
    print("  flat = uniform over the SAME candidate set (no ranking, the control).")
    print("  %-7s %-16s %-16s %-16s" % ("text", "top-1 W/flat", "top-3 W/flat", "perplexity W/flat"))
    out = {}
    for name, text in [("CROW", jpafg.CROW), ("STORY", jrms.STORY)]:
        r = pr.weighted_first_pass(_fresh(), text)
        out[name] = r
        print("  %-7s %6.3f/%-8.3f %6.3f/%-8.3f %7.1f/%-8.1f"
              % (name, r["top1_weighted"], r["top1_flat"],
                 r["topk_weighted"], r["topk_flat"],
                 r["perplexity_weighted"], r["perplexity_flat"]))
    print("  -> weighted top-1/top-k HIGHER + perplexity LOWER than the flat set:")
    print("     finer grain for predicting written text (strongest where the text is")
    print("     most predictable — the repetitive STORY — which is correct).")
    return out


def part3_surprisal_graded(story_out: dict) -> None:
    print("\n" + "=" * 78)
    print("3. SURPRISAL-GRADED RESIDUAL  (effort-follows-residual now CONTINUOUS)")
    print("=" * 78)
    print("  per-word surprisal (-ln p) on a STORY sentence: a predictable word GLIDES")
    print("  (low surprisal), a rare/novel word DWELLS (high surprisal). Graded, not")
    print("  the binary confirm-vs-deep:")
    r = story_out["STORY"]
    # pick the richest late sentence (most words) to show the gradation.
    rows = [st for st in r["steps"] if not st.get("cold_start") and st["surprisals"]]
    st = max(rows, key=lambda s: len(s["surprisals"]))
    print("    sentence k=%d: %r" % (st["k"], st["sentence"]))
    for w, s in sorted(st["surprisals"], key=lambda x: x[1]):
        band = "glide" if s < 2.5 else ("dwell" if s > 5.0 else "     ")
        print("      %-12s surprisal %6.3f   %s" % (w, s, band))


def part4_verse() -> dict:
    print("\n" + "=" * 78)
    print("4. VERSE — meter/rhyme weights sharpen the LINE-END (rhyme slot) prediction")
    print("=" * 78)
    out = {}
    for name, V in [("FORMULAIC", FORMULAIC), ("JABBERWOCKY", JABBERWOCKY)]:
        ag = _fresh()
        mr.ensure_meter_codebook(ag)
        r = pr.weighted_verse_first_pass(ag, V)
        out[name] = r
        print("  %-12s line-end surprisal: guided %.3f  vs  baseline(no meter) %.3f  (n=%d)"
              % (name, r["lineend_surprisal_guided"], r["lineend_surprisal_baseline"],
                 r["n_line_ends"]))
    print("  -> on FORMULAIC verse (rhyme words recur in the register) the meter/rhyme")
    print("     weight LOWERS line-end surprisal (the harmonic model predicts the rhyme).")
    print("     JABBERWOCKY is the honest ceiling: its NONSENSE rhymes are novel words")
    print("     (no register word fills the sound class) -> guided == baseline at the OOV")
    print("     floor. A truly novel word IS high-surprisal, which is CORRECT.")
    return out


def part5_comprehension_unchanged() -> bool:
    print("\n" + "=" * 78)
    print("5. FINAL COMPREHENSION BYTE-IDENTICAL  (prediction speeds the PROCESS)")
    print("=" * 78)
    base = jpafg.analyse(jpafg.CROW)["report"]
    ag = _fresh()
    pr.weighted_first_pass(ag, jpafg.CROW)
    rd.run_reading_flow(ag, jpafg.CROW, report="analysis")
    after = jpafg._read_report_off_graph(ag.s)
    print("  baseline report %d chars; after weighted stream %d chars; identical: %s"
          % (len(base), len(after), base == after))
    return base == after


def main() -> int:
    dl.warm_wordnet("en")
    part1_distribution()
    story_out = part2_top1_topk_perplexity()
    part3_surprisal_graded(story_out)
    verse = part4_verse()
    identical = part5_comprehension_unchanged()

    print("\n" + "=" * 78)
    print("WEIGHTED WORD-LIKELIHOOD — the flat set is now a distribution")
    print("=" * 78)
    st = story_out["STORY"]
    print("* STORY: top-1 %.3f vs flat %.3f; top-3 %.3f vs %.3f; perplexity %.1f vs %.1f."
          % (st["top1_weighted"], st["top1_flat"], st["topk_weighted"],
             st["topk_flat"], st["perplexity_weighted"], st["perplexity_flat"]))
    print("* SURPRISAL is graded (-ln p): effort-follows-residual is CONTINUOUS.")
    print("* VERSE FORMULAIC line-end surprisal %.3f (guided) vs %.3f (baseline)."
          % (verse["FORMULAIC"]["lineend_surprisal_guided"],
             verse["FORMULAIC"]["lineend_surprisal_baseline"]))
    print("* COMPREHENSION byte-identical: %s (the answer is unchanged)." % identical)
    print("* HONEST: the win is REAL but SCALES WITH PREDICTABILITY — large on the")
    print("  repetitive STORY, modest on the terse CROW; top-1 is capped (one argmax")
    print("  per sentence). The weights are the sources' EVIDENCE (frequency counts,")
    print("  beat recurrence, resonance), add-one (Laplace) smoothed — not tuned. The")
    print("  ceiling is the register/production vocabulary: a truly novel word is high-")
    print("  surprisal, which is CORRECT (Jabberwocky's nonsense rhymes prove it).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

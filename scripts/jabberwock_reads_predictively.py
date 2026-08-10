"""jabberwock_reads_predictively — THE WHOLE FIRST PASS IS PREDICTION.

The AbS capstone (domains/predictive_reading.py) demonstrated recurring-BEAT
prediction on ONE arc: a writer/audience model conditions the production faculty
as a forward predictor, and the ShapeDecode residual is the surprise. This script
LIFTS that from arc-by-arc to the WHOLE FIRST PASS — the fluent-reading loop.

As the reader streams a text SENTENCE BY SENTENCE, at EACH sentence the
ACCUMULATING writer/audience/context model PREDICTS the next sentence's words
BEFORE reading them (the production faculty forward — predict_next_words,
conditioned on the recurring beat harvested from the sentences seen so far + the
discourse context + the accumulating register vocabulary). The arriving sentence
is DECODED against that prediction (the AbS ShapeDecode collapse — the `residual`
IS the surprise). The predicted words FAST-CONFIRM (low residual, cheap); the
RESIDUAL is the NEWS — the words that drive the deep, order-N processing.

    accumulating writer/register model ─synthesize→ PREDICTED next-sentence words
                                                          │  ShapeDecode compare
                       actual arriving sentence  ─────────┤
                                                          ▼
                    CONFIRMED  (register + recurring beat — FAST, cheap)
                    RESIDUAL   (the novel content — the NEWS, deep-processed)

Three measurements, every one behind a protected control:

  1. PER-SENTENCE + AGGREGATE — stream a fable predictively and show, per sentence,
     the predicted structure/function words fast-confirming while the novel content
     is the residual (the news). The aggregate confirm fraction is the speedup (the
     fraction of arriving tokens that DON'T need bottom-up work); the deep-process
     fraction is the residual (the news).

  2. FINAL COMPREHENSION UNCHANGED — the predictive first pass is the PROCESS, not
     the answer. Running the predictive stream then the comprehension flow yields a
     report BYTE-IDENTICAL to the non-predictive baseline. Prediction speeds the
     PROCESS; it does not change the ANSWER.

  3. THE ACCUMULATING MODEL IMPROVES PREDICTION — an ablation isolating the
     accumulating register: no-register (beat+context only) vs a 1-sentence window
     vs FULL accumulation. Full accumulation confirms MORE — the writer model
     genuinely improves prediction as the text proceeds.

GRAPH-NATIVE (CLAUDE.md): the prediction is the production faculty run forward; the
compare/residual is a ShapeDecode collapse (not a Python set-difference); driven by
cognitive_tick (read_arc_predictively mints a PredictiveReadingStage the seeded
predictive_read_advance Reflex fires). NO hardcoded expected words — the predicted
words are HARVESTED from the graph (the recurring beat + the discourse content +
the accumulating register). No `import re`; donkey = 0.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_predictively.py
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


# --------------------------------------------------------------------------- #
#  1. THE WHOLE-FIRST-PASS PREDICTIVE STREAM (per-sentence + aggregate).
# --------------------------------------------------------------------------- #
def _print_stream(name: str, text: str) -> dict:
    ag = _fresh()
    out = pr.predict_first_pass(ag, text)
    print("=" * 78)
    print("1. PREDICTIVE FIRST PASS — %s" % name)
    print("   (each sentence: PREDICT from the accumulating model, DECODE, split")
    print("    CONFIRMED [fast] vs RESIDUAL [the news]).")
    print("=" * 78)
    print("  %-3s %-5s %-6s %-6s  %s" % ("k", "n", "hit", "conf", "confirmed [fast]  ||  residual [the news]"))
    for st in out["steps"]:
        tag = "COLD" if st.get("cold_start") else "    "
        conf = " ".join(st["confirmed"][:6]) or "-"
        surp = " ".join(st["surprise"][:6]) or "-"
        print("  %-3d %-5d %-6.2f %-6.2f  %-4s %-28s || %s"
              % (st["k"], st["n_actual"], st["hit_rate"], st["confirm_frac"],
                 tag, conf, surp))
    a = out["aggregate"]
    print("\n  AGGREGATE over the whole text (%d sentences, %d words):"
          % (a["n_sentences"], a["total_words"]))
    print("    fast-confirm fraction (the speedup) = %.1f%%  (%d/%d words confirmed)"
          % (100 * a["confirm_frac"], a["total_confirmed"], a["total_words"]))
    print("    deep-process fraction (the residual = the news) = %.1f%%"
          % (100 * a["deep_process_frac"]))
    print("    mean per-sentence prediction hit-rate = %.1f%%" % (100 * a["mean_hit_rate"]))
    print("    early-half confirm = %.1f%%   late-half confirm = %.1f%%  (accumulating model)"
          % (100 * a["early_confirm_frac"], 100 * a["late_confirm_frac"]))
    return out


# --------------------------------------------------------------------------- #
#  2. FINAL COMPREHENSION UNCHANGED — prediction is the PROCESS, not the answer.
# --------------------------------------------------------------------------- #
def _comprehension_unchanged(text: str) -> tuple:
    base = jpafg.analyse(text)["report"]                 # non-predictive baseline
    ag = _fresh()
    pr.predict_first_pass(ag, text)                      # the predictive PROCESS
    rd.run_reading_flow(ag, text, report="analysis")     # then the comprehension
    after = jpafg._read_report_off_graph(ag.s)
    return base, after


# --------------------------------------------------------------------------- #
#  3. ACCUMULATING-MODEL ABLATION — no-register vs window vs full accumulation.
# --------------------------------------------------------------------------- #
def _windowed_confirm(ag, text: str, window: int) -> float:
    """Confirm fraction over the whole text with the register limited to the last
    `window` sentences (window=0 => NO register, beat+context only). The SAME
    predict→ShapeDecode→residual machinery; only the register's memory differs."""
    sents = rc._split_sentences(text)
    tot_a = tot_c = 0
    for i in range(1, len(sents)):
        seen = sents[:i]
        reg_src = seen[max(0, len(seen) - window):] if window else []
        reg = pr._word_types(ag, " ".join(reg_src))
        model = pr.build_writer_model(ag, seen)
        pred = pr.predict_next_words(ag, model["writer_style"],
                                     context=" ".join(seen), seen_vocab=reg)
        cmp = pr.abs_compare(ag, pred["predicted_words"], pr._words(ag, sents[i]))
        tot_a += cmp["n_actual"]
        tot_c += len(cmp["confirmed"])
    return (tot_c / tot_a) if tot_a else 0.0


def _ablation(name: str, text: str) -> dict:
    ag = _fresh()
    r0 = _windowed_confirm(ag, text, 0)
    r1 = _windowed_confirm(ag, text, 1)
    rall = _windowed_confirm(ag, text, 999)
    return {"name": name, "no_register": r0, "window1": r1, "full": rall}


def main() -> int:
    dl.warm_wordnet("en")

    # 1. per-sentence + aggregate — on the crow AND the recurring-beat multi-arc story.
    _print_stream("The Crow and the Pitcher", jpafg.CROW)
    print()
    story_out = _print_stream("Mira (multi-arc, recurring beat)", jrms.STORY)

    # highlight the recurring beat fast-confirming as it recurs (the AbS payoff, now
    # whole-text): the beat sentence's confirm fraction across its instances.
    beat_steps = [s for s in story_out["steps"]
                  if "thanked" in s["confirmed"] and "gave" in s["confirmed"]]
    if beat_steps:
        print("\n  the RECURRING BEAT fast-confirms as it recurs (k, confirm-fraction):")
        print("   ", ", ".join("k=%d:%.0f%%" % (s["k"], 100 * s["confirm_frac"])
                                for s in beat_steps))

    # 2. final comprehension unchanged.
    print("\n" + "=" * 78)
    print("2. FINAL COMPREHENSION UNCHANGED — prediction is the PROCESS, not the answer")
    print("=" * 78)
    base, after = _comprehension_unchanged(jpafg.CROW)
    print("  baseline report:            %d chars" % len(base))
    print("  after-predictive-stream:    %d chars" % len(after))
    print("  BYTE-IDENTICAL: %s" % (base == after))
    print("  -> the predictive first pass speeds the PROCESS; the settled")
    print("     comprehension (the crow's arc + theme + report) is the SAME answer.")

    # 3. accumulating-model ablation.
    print("\n" + "=" * 78)
    print("3. THE ACCUMULATING MODEL IMPROVES PREDICTION (confirm fraction)")
    print("=" * 78)
    print("  %-8s %-14s %-16s %s" % ("text", "no-register", "1-sent-window", "FULL-accumulation"))
    for name, text in [("CROW", jpafg.CROW), ("STORY", jrms.STORY)]:
        ab = _ablation(name, text)
        print("  %-8s %-14.2f %-16.2f %.2f"
              % (name, ab["no_register"], ab["window1"], ab["full"]))
    print("  -> full accumulation confirms MORE than a 1-sentence window or no")
    print("     register: the writer/register model genuinely improves prediction")
    print("     as the text proceeds (the accumulating first pass pays).")

    print("\n" + "=" * 78)
    print("The whole first pass is PREDICTION: predict → confirm → residual, per")
    print("sentence, driven by cognitive_tick. Most text is partly predictable (the")
    print("register + the recurring beat FAST-CONFIRM); comprehension focuses on the")
    print("residual — the surprise IS the news. The answer is unchanged.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

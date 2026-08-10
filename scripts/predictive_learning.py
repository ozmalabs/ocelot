"""predictive_learning — the culminating speech experiment: the agent shapes
its OWN representation by how well its units PREDICT the next unit, on real
continuous speech, with NO labels and NO recognition accuracy in the loop.

THE THESIS (memory: compression/prediction as the quality signal, curiosity
drives the substrate). Every perception/recognition lever this session was
marginal on the 10-digit toy (~56-61% plateau). The ONE genuinely non-marginal
capability is structure-learning from sentences: next-unit prediction beats the
agent's own frequency baseline and COLLAPSES under shuffle (real sequential
structure). So the objective to optimise is PREDICTION, not accuracy.

WHAT THIS SCRIPT DOES
  1. SCALE: ingest a large LibriSpeech set (many utts / many speakers) through
     the agent's OWN perception (STTPipeline.ingest), reading out the ordered
     sign-id sequence per utterance. Signs recur via the pipeline's DTW merge —
     the `value` key IS the agent's unit identity. (perception_self_assessment.
     read_unit_sequences is exactly this.)

  2. OBJECTIVE = the agent's prediction/compression signal
     (perception_self_assessment.measure_unit_predictability): held-out next-unit
     predict_over_FREQUENCY + compression, with the SHUFFLE control. The single
     number the agent optimises is the HONEST one — predict_over_freq (bigram
     beats the units' OWN frequency baseline), NOT the inflated over-chance
     number. The polluted-lexicon trap (a smaller/skewed lexicon inflates the
     frequency baseline and the raw top-1 while over-freq/shuffle stay flat) is
     exactly why we read over-freq, not raw top-1.

  3. THE AGENT OPTIMISES ITS REPRESENTATION FOR PREDICTION (curiosity drive AS
     objective): sweep the levers that shape its units —
       - GRANULARITY: the DTW/merge threshold (la_distance_threshold). Coarser /
         finer threshold -> coarser / finer lexicon -> different predictability.
       - REPRESENTATION: which ear (gammatone default vs the warped formant-dense
         front-end) feeds the unit DTW.
     For each candidate we ingest the corpus and measure the objective on a
     held-out split. The agent KEEPS the candidate whose held-out predict_over_freq
     is highest — selection BY ITS OWN compression signal, not hand-picked. The
     pick is enacted graph-resident: the candidates are written as
     PerceptionQuality assessments under the PerceptionSelfRoot and the winner is
     the argmax over predict_over_freq (the same yardstick the frontier rule uses).

  4. LEARNING CURVE: with the chosen representation fixed, measure the objective
     on growing PREFIXES of the corpus (no re-ingest) — does predict_over_freq
     RISE with more sentences (more structure learned) or PLATEAU?

HONEST TEST. The deliverable is a clear curve — even a plateau. We do NOT tune to
manufacture a rise. The controls (frequency baseline + shuffle) must hold for the
result to be real, not an artifact.

Run:
    python -m scripts.predictive_learning [n_utts] [n_speakers]

NB: each (threshold, representation) candidate is a FULL ingest pass because the
lexicon is built STREAMING at the merge threshold (a different threshold mints a
different lexicon). So total cost ~= n_candidates * n_utts * ~0.5s. Sized to
finish well under an hour at the defaults; pass smaller n_utts to go faster.
"""
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams
from domains.perception_self_assessment import (
    measure_unit_predictability,
    record_perception_quality,
    install_perception_frontier_rule,
    agent_flag_perception,
)
import scripts.sentence_learning as SL


# Granularity sweep — DTW/merge thresholds around the default 0.02. Coarser
# (larger) merges more aggressively -> smaller lexicon; finer (smaller) keeps
# units distinct -> larger lexicon. The agent's tune-Rule would search exactly
# this dial; here we enumerate a few and let the objective pick.
THRESHOLD_SWEEP = [0.008, 0.015, 0.02, 0.035, 0.06]

# Representations (which "ear" feeds the unit DTW): the default gammatone log
# cochlea vs the warped formant-dense front-end (more bands + A1 patches where
# F1/F2 live). Same gammatone primitive, different band layout.
REPRESENTATIONS = ["gammatone", "warped"]


def _params(representation: str, threshold: float) -> STTParams:
    if representation == "warped":
        return STTParams.warped(sample_rate=8000,
                                la_distance_threshold=float(threshold))
    return STTParams(sample_rate=8000, la_distance_threshold=float(threshold))


def ingest_corpus(sel, representation: str, threshold: float,
                  log_every: int = 200):
    """Ingest the whole selection through ONE fresh substrate with the given
    representation + merge threshold, returning the per-utterance ordered
    sign-id sequences (the agent's OWN units). Streaming lexicon: the threshold
    shapes which signs merge as we go, so this must be a fresh pass per
    candidate. Mechanical world-adapter readout — no agent reasoning here."""
    sub = Substrate()
    pipe = STTPipeline(_params(representation, threshold))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    sequences = []
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        try:
            samples, _ = SL.load_flac_8k(path)
        except Exception:
            continue
        try:
            signs = pipe.ingest(sub, samples)
        except Exception:
            continue
        sub.tick(50000)
        seq = []
        for s in signs:
            v = getattr(s, "value", None)
            seq.append(v if v is not None else repr(s))
        if len(seq) >= 2:
            sequences.append(seq)
        if (i + 1) % log_every == 0:
            print(f"    [{representation} thr={threshold:.3f}] "
                  f"{i + 1}/{len(sel)} utts  seqs={len(sequences)}  "
                  f"({time.time() - t0:.0f}s)", flush=True)
    return sequences, sub


def shuffle_objective(sequences, seed: int = 7) -> dict:
    """The SHUFFLE control: pool all unit tokens, shuffle (kills order, keeps
    frequency), re-chunk to the same per-utt lengths, and measure the SAME
    objective. Real sequential structure must COLLAPSE here. Returns the same
    signal dict so we can compare predict_over_freq / predict_top1."""
    rng = random.Random(seed)
    seqs = [list(s) for s in sequences if len(s) >= 2]
    all_tokens = [t for s in seqs for t in s]
    lengths = [len(s) for s in seqs]
    rng.shuffle(all_tokens)
    shuf = []
    idx = 0
    for L in lengths:
        shuf.append(all_tokens[idx:idx + L])
        idx += L
    return measure_unit_predictability(shuf, seed=seed)


def main():
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 40

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    print(f"LibriSpeech dev-clean: {len(pairs)} utterances, "
          f"{len(speakers)} speakers")
    chosen_spk = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen_spk]
    random.shuffle(sel)
    sel = sel[:n_utts]
    used_spk = sorted(set(p[1] for p in sel))
    print(f"Using {len(sel)} utterances from {len(used_spk)} speakers")
    print(f"Granularity sweep: {THRESHOLD_SWEEP}")
    print(f"Representations  : {REPRESENTATIONS}")
    n_candidates = len(THRESHOLD_SWEEP) * len(REPRESENTATIONS)
    print(f"=> {n_candidates} full ingest passes "
          f"(~{n_candidates * len(sel) * 0.45 / 60:.0f} min projected)\n",
          flush=True)

    # -----------------------------------------------------------------
    # (1) THE GRANULARITY x REPRESENTATION SWEEP. Each candidate is a full
    # ingest; we measure the OBJECTIVE (held-out predict_over_freq +
    # compression) on the agent's own units, plus the shuffle control.
    # The agent KEEPS the candidate with the highest held-out predict_over_freq.
    # -----------------------------------------------------------------
    print("==================================================")
    print("(1) GRANULARITY x REPRESENTATION SWEEP")
    print("    objective = held-out predict_over_freq (HONEST: bigram beats")
    print("    the units' OWN frequency baseline). selection = argmax of it.")
    print("==================================================")
    header = (f"{'repr':>10} {'thresh':>7} {'lexicon':>8} {'tokens':>7} "
              f"{'recur':>6} {'over_freq':>9} {'over_chance':>11} "
              f"{'compress':>8} {'shuf_ofreq':>10} {'verdict':>8}")
    print(header)
    print("-" * len(header))

    results = []          # one dict per candidate
    best_seqs = None      # captured sequences of the winning candidate
    for representation in REPRESENTATIONS:
        for thr in THRESHOLD_SWEEP:
            seqs, _sub = ingest_corpus(sel, representation, thr)
            if len(seqs) < 10:
                print(f"{representation:>10} {thr:>7.3f}   "
                      f"(too few sequences: {len(seqs)}) — skipped")
                continue
            sig = measure_unit_predictability(seqs, seed=7)
            shuf = shuffle_objective(seqs, seed=7)
            # honest verdict per candidate: real iff it beats its own frequency
            # baseline AND the shuffle collapses (order, not artifact).
            beats_freq = sig["predict_over_freq"] >= 1.10
            collapses = shuf["predict_over_freq"] < sig["predict_over_freq"] * 0.9
            verdict = "REAL" if (beats_freq and collapses) else "artifact?"
            rec = {
                "representation": representation,
                "threshold": thr,
                "sequences": seqs,
                "signal": sig,
                "shuffle": shuf,
                "verdict": verdict,
            }
            results.append(rec)
            print(f"{representation:>10} {thr:>7.3f} "
                  f"{sig['lexicon_size']:>8d} {sig['n_tokens']:>7d} "
                  f"{sig['recurrence']:>6.3f} "
                  f"{sig['predict_over_freq']:>9.3f} "
                  f"{sig['predict_over_chance']:>11.2f} "
                  f"{sig['compress_ratio']:>8.3f} "
                  f"{shuf['predict_over_freq']:>10.3f} "
                  f"{verdict:>8}", flush=True)

    if not results:
        print("\nNo candidate produced enough sequences. Aborting.")
        return

    # -----------------------------------------------------------------
    # (1b) THE AGENT PICKS — graph-resident argmax over predict_over_freq.
    # Write each candidate's objective as a PerceptionQuality assessment under
    # the PerceptionSelfRoot (the agent's own yardstick node), then select the
    # winner by the same signal the frontier rule judges by. Selection is by the
    # agent's compression/prediction signal, not by us.
    # -----------------------------------------------------------------
    sub = Substrate()
    quality_nodes = []
    for rec in results:
        q = record_perception_quality(sub, rec["signal"])
        sub.set_attr(q, "cand_representation", rec["representation"])
        sub.set_attr(q, "cand_threshold", float(rec["threshold"]))
        quality_nodes.append((q, rec))
    # argmax over the honest objective, read straight from graph state.
    best_q, best_rec = max(
        quality_nodes,
        key=lambda qr: float(sub.node(qr[0])["attrs"]["predict_over_freq"]))
    best_seqs = best_rec["sequences"]
    # Install the frontier rule + fire it on the winner's assessment so the
    # agent's own judgement (is this representation's perception still poor?)
    # is on record, graph-resident.
    fr = install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "predict_over_freq",
                 float(best_rec["signal"]["predict_over_freq"]))
    sub.set_attr(root, "compress_ratio",
                 float(best_rec["signal"]["compress_ratio"]))
    sub.set_attr(root, "perception_quality_pending", 1)
    frontier = agent_flag_perception(sub, fr["rule_index"])

    default_rec = next(
        (r for r in results
         if r["representation"] == "gammatone" and abs(r["threshold"] - 0.02) < 1e-9),
        None)

    print("\n==================================================")
    print("(1c) AGENT'S SELECTION (by its own prediction signal)")
    print("==================================================")
    print(f"CHOSEN representation : {best_rec['representation']}  "
          f"threshold {best_rec['threshold']:.3f}")
    print(f"  predict_over_freq   : {best_rec['signal']['predict_over_freq']:.3f}  "
          f"(the objective it maximised)")
    print(f"  compress_ratio      : {best_rec['signal']['compress_ratio']:.3f}  "
          f"(lower = more compressible = better)")
    print(f"  lexicon size        : {best_rec['signal']['lexicon_size']}")
    print(f"  shuffle over_freq    : {best_rec['shuffle']['predict_over_freq']:.3f}  "
          f"(control — must be << chosen)")
    print(f"  agent frontier flag : {frontier}  "
          f"(does the agent still judge its perception poor?)")
    if default_rec is not None:
        d = default_rec["signal"]
        print(f"DEFAULT (gammatone/0.02): predict_over_freq {d['predict_over_freq']:.3f}, "
              f"compress {d['compress_ratio']:.3f}, lexicon {d['lexicon_size']}")
        delta = best_rec["signal"]["predict_over_freq"] - d["predict_over_freq"]
        print(f"  CHOSEN - DEFAULT over_freq: {delta:+.3f}  "
              f"({'beats default' if delta > 0.02 else 'no material gain over default'})")

    # -----------------------------------------------------------------
    # (2) LEARNING CURVE — chosen representation fixed, objective vs corpus
    # size. We sub-sample growing PREFIXES of the winner's captured sequences
    # (no re-ingest). Does more data -> more structure (rising predict_over_freq)
    # or a plateau? Honest: we report the curve as-is.
    # -----------------------------------------------------------------
    print("\n==================================================")
    print("(2) LEARNING CURVE (chosen representation, growing corpus)")
    print(f"    representation={best_rec['representation']} "
          f"threshold={best_rec['threshold']:.3f}")
    print("==================================================")
    n = len(best_seqs)
    fractions = [0.1, 0.25, 0.5, 0.75, 1.0]
    print(f"{'n_utts':>7} {'lexicon':>8} {'tokens':>7} {'over_freq':>9} "
          f"{'over_chance':>11} {'compress':>8} {'info_gain':>9}")
    curve = []
    for frac in fractions:
        k = max(2, int(frac * n))
        sub_seqs = best_seqs[:k]
        sig = measure_unit_predictability(sub_seqs, seed=7)
        curve.append((k, sig))
        print(f"{len(sub_seqs):>7d} {sig['lexicon_size']:>8d} "
              f"{sig['n_tokens']:>7d} {sig['predict_over_freq']:>9.3f} "
              f"{sig['predict_over_chance']:>11.2f} "
              f"{sig['compress_ratio']:>8.3f} {sig['info_gain_bits']:>9.3f}",
              flush=True)

    # -----------------------------------------------------------------
    # (3) CONTROLS on the chosen representation at FULL scale:
    #     chosen vs frequency baseline vs SHUFFLE. Must beat frequency AND
    #     collapse under shuffle to be real.
    # -----------------------------------------------------------------
    full = best_rec["signal"]
    shuf = best_rec["shuffle"]
    print("\n==================================================")
    print("(3) CONTROLS (chosen representation, full corpus)")
    print("==================================================")
    print(f"chosen predict_top1      : {full['predict_top1']:.4f}")
    print(f"frequency baseline top1  : {full['predict_freq_baseline']:.4f}  "
          f"(most-common next unit, NO context)")
    print(f"predict_over_freq        : {full['predict_over_freq']:.3f}  "
          f"(>1.10 => context beats raw frequency)")
    print(f"SHUFFLED predict_over_freq: {shuf['predict_over_freq']:.3f}  "
          f"(order destroyed; must collapse toward 1.0)")
    print(f"shuffle predict_top1     : {shuf['predict_top1']:.4f}")
    beats_freq = full["predict_over_freq"] >= 1.10
    collapses = shuf["predict_over_freq"] < full["predict_over_freq"] * 0.9
    print(f"beats frequency          : {'YES' if beats_freq else 'NO'}")
    print(f"collapses under shuffle  : {'YES' if collapses else 'NO'} "
          f"({full['predict_over_freq']:.3f} -> {shuf['predict_over_freq']:.3f})")

    # -----------------------------------------------------------------
    # HONEST VERDICT.
    # -----------------------------------------------------------------
    over_freqs = [(r["representation"], r["threshold"],
                   r["signal"]["predict_over_freq"]) for r in results]
    spread = (max(o[2] for o in over_freqs)
              - min(o[2] for o in over_freqs))
    # learning-curve direction: last vs first measured point.
    lc_first = curve[0][1]["predict_over_freq"]
    lc_last = curve[-1][1]["predict_over_freq"]
    rising = lc_last > lc_first + 0.03
    print("\n==================================================")
    print("HONEST VERDICT — does prediction-as-objective work?")
    print("==================================================")
    print(f"(i)   real (beats freq + collapses on shuffle) : "
          f"{'YES' if (beats_freq and collapses) else 'NO'}")
    if default_rec is not None:
        d = default_rec["signal"]["predict_over_freq"]
        better = best_rec["signal"]["predict_over_freq"] - d
        print(f"(ii)  optimisation beats the default          : "
              f"{'YES' if better > 0.02 else 'NO'} "
              f"(chosen {best_rec['signal']['predict_over_freq']:.3f} vs "
              f"default {d:.3f}, +{better:.3f})")
    print(f"(iii) objective rises with more sentences      : "
          f"{'YES' if rising else 'NO / PLATEAU'} "
          f"({lc_first:.3f} @ {curve[0][0]} utts -> "
          f"{lc_last:.3f} @ {curve[-1][0]} utts)")
    print(f"      sweep spread in predict_over_freq        : {spread:.3f}  "
          f"(how much the representation lever moves the objective)")
    print()
    print("READ: prediction-as-objective is REAL iff (i) holds. It drives a")
    print("MATERIALLY better representation iff (ii) holds. It keeps learning")
    print("with scale iff (iii) rises; a flat curve is an honest PLATEAU — the")
    print("structure the bigram-over-units objective can capture is saturated,")
    print("and the next lever is a richer model/representation, not more data.")


if __name__ == "__main__":
    main()

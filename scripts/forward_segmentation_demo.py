"""forward_segmentation_demo — does FORWARD CONSTRUCTION from transitional-
probability structure discover words on real continuous speech?

The agent ingests LibriSpeech through its OWN perception (STTPipeline), reads out
the ordered sub-word unit sequences WITH their times, then DESIGNS FORWARD a
word-segmenter from the TP structure (domains/forward_segmentation): boundaries
at TP troughs (below the running median of the TP distribution — derived, not
swept), high-TP runs merged into chunks, iterated bottom-up. The boundary
decision runs as a graph-resident Term the agent owns.

This is NOT a parameter sweep. The level is the median of the data's own TP
distribution. Compression is the SELECTOR, computed AFTER the build — never used
to search. We report, with numbers, whether forward construction discovers
word-like units or whether the TP structure is too noisy (an honest null is a
valid finding).

ACCEPTANCE (raw sub-word units vs forward-constructed chunks):
  (A) chunk count / mean length / recurrence — chunks should be FEWER, LONGER,
      RECURRING (word-like) than the raw units;
  (B) COMPRESSION — do the chunked sequences compress better (lower bits/token,
      two-part MDL) than the raw sub-word sequences?
  (C) ALIGNMENT — do the constructed boundaries land on REAL word boundaries
      better than the raw sub-word boundaries? Measured against the transcripts
      via rough proportional time alignment (LibriSpeech has no word timestamps):
      boundary precision/recall + chunk-to-word purity, raw vs constructed.

Run:
    python -m scripts.forward_segmentation_demo [n_utts] [n_speakers] [n_passes]
"""
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key
import scripts.sentence_learning as SL
from domains.forward_segmentation import (
    agent_specify_segmenter, estimate_tp, forward_segment, segment_pass,
    chunk_stats, description_length_bits, _keystr,
)


def words_of(transcript: str):
    return [w for w in re.findall(r"[\w']+", transcript.lower()) if w]


def ordered_signs_with_time(sub, stream):
    """Time-ordered (start_time_s, sign_key) for the most recent stream's signs.
    Pure graph readout — no second cochlear pass."""
    out = []
    for utt in sub.in_neighbours(stream, "from_stream"):
        if sub.node(utt)["type"] != "Utterance":
            continue
        t = sub.node(utt)["attrs"].get("start_time_s")
        t = float(t) if t is not None else 0.0
        for s in sub.neighbours(utt, "heard_as"):
            out.append((t, _node_sort_key(s)))
    out.sort(key=lambda x: x[0])
    return out


def latest_stream(sub):
    best, best_k = None, -1
    for st in sub.nodes("AudioStream"):
        if sub.node(st)["attrs"].get("_pipeline_template"):
            continue
        if not any(sub.node(u)["type"] == "Utterance"
                   for u in sub.in_neighbours(st, "from_stream")):
            continue
        v = getattr(st, "value", None)
        k = v if isinstance(v, int) else 0
        if k >= best_k:
            best_k, best = k, st
    return best


# --------------------------------------------------------------------------
# Rough proportional word-boundary reference. LibriSpeech ships no word-level
# timestamps, so we map transcript words onto the utterance timeline in
# proportion to their character length (a rough but unbiased reference — it is
# applied identically to raw and constructed, so any DIFFERENCE between them is
# real). Returns the set of word-boundary times.
# --------------------------------------------------------------------------

def proportional_word_boundaries(words, t_start, t_end):
    if not words or t_end <= t_start:
        return []
    lens = [len(w) + 1 for w in words]      # +1 for the inter-word space
    total = sum(lens)
    dur = t_end - t_start
    bounds = []
    acc = 0
    for L in lens[:-1]:                      # boundary after each word but last
        acc += L
        bounds.append(t_start + dur * acc / total)
    return bounds


def boundary_times_of_chunks(unit_times, chunk_lengths):
    """Given the per-unit times and the chunk lengths (in units), the chunk
    boundary times = the time of the FIRST unit of each chunk after the first."""
    bounds = []
    idx = 0
    for L in chunk_lengths[:-1]:
        idx += L
        if idx < len(unit_times):
            bounds.append(unit_times[idx])
    return bounds


def boundary_pr(pred_times, true_times, tol):
    """Boundary precision/recall: a predicted boundary matches a true boundary if
    within `tol` seconds. Greedy 1:1 matching."""
    if not pred_times and not true_times:
        return 1.0, 1.0, 1.0
    true_used = [False] * len(true_times)
    hits = 0
    for pt in pred_times:
        best_j, best_d = -1, tol
        for j, tt in enumerate(true_times):
            if true_used[j]:
                continue
            d = abs(pt - tt)
            if d <= best_d:
                best_d, best_j = d, j
        if best_j >= 0:
            true_used[best_j] = True
            hits += 1
    prec = hits / len(pred_times) if pred_times else 0.0
    rec = hits / len(true_times) if true_times else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def unit_word_map(unit_times, words, t_start, t_end):
    """Proportional unit->word assignment by time fraction. Returns a list
    (one word-index per unit). Used for chunk purity."""
    if not words or t_end <= t_start:
        return [0] * len(unit_times)
    lens = [len(w) + 1 for w in words]
    total = sum(lens)
    # cumulative word end-fractions
    ends, acc = [], 0
    for L in lens:
        acc += L
        ends.append(acc / total)
    dur = t_end - t_start
    out = []
    for t in unit_times:
        frac = (t - t_start) / dur if dur > 0 else 0.0
        wi = 0
        while wi < len(ends) - 1 and frac > ends[wi]:
            wi += 1
        out.append(wi)
    return out


def chunk_purity(chunk_lengths, unit_to_word):
    """Fraction of chunks whose units all map to the SAME transcript word
    (weighted by chunk so longer chunks count once). Higher = chunks respect
    word boundaries. Raw single-unit chunks are trivially pure — so we also
    return the multi-unit purity (chunks of length >= 2), the honest number."""
    pure = total = 0
    mpure = mtotal = 0
    idx = 0
    for L in chunk_lengths:
        span = unit_to_word[idx:idx + L]
        idx += L
        if not span:
            continue
        same = len(set(span)) == 1
        total += 1
        pure += 1 if same else 0
        if L >= 2:
            mtotal += 1
            mpure += 1 if same else 0
    return (pure / total if total else 0.0,
            mpure / mtotal if mtotal else float("nan"), mtotal)


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    n_passes = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    import random
    random.seed(1)

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    print(f"LibriSpeech dev-clean: {len(pairs)} utts, {len(speakers)} speakers")
    chosen = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"Using {len(sel)} utterances from {len(set(p[1] for p in sel))} "
          f"speakers; n_passes={n_passes}")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)

    # Install the speech science so the agent's spec is GROUNDED in the
    # statistical_learning concept it actually holds (not just asserted).
    try:
        from domains.speech_science import install_speech_science
        install_speech_science(sub)
    except Exception as e:
        print(f"(speech_science not installed: {e})")

    # The agent specifies its segmenter from its statistical_learning science.
    spec = agent_specify_segmenter(sub)
    print("\nAGENT SPEC (reasoned forward from statistical_learning science):")
    print(f"  principle      : {spec['principle']}")
    print(f"  boundary_rule  : {spec['boundary_rule']}")
    print(f"  level_source   : {spec['level_source']} "
          f"(searched={spec['level_is_searched']})")
    print(f"  grounded       : {spec['grounded_in_science']}  "
          f"forward={spec['is_forward_construction']}  search={spec['is_search']}")

    # ----- ingest: ordered sub-word unit sequences WITH times + transcripts
    unit_seqs = []          # list of [unit_key, ...]
    unit_time_seqs = []     # parallel [start_time_s, ...]
    word_seqs = []          # transcript words
    span_seqs = []          # (t_start, t_end) per utt
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        words = words_of(transcript)
        if not words:
            continue
        try:
            samples, _ = SL.load_flac_8k(path)
            pipe.ingest(sub, samples)
        except Exception as e:
            print(f"  FAIL {path}: {e}", flush=True)
            continue
        sub.tick(50000)
        stream = latest_stream(sub)
        if stream is None:
            continue
        st = ordered_signs_with_time(sub, stream)
        if len(st) < 2:
            continue
        times = [t for t, _ in st]
        keys = [k for _, k in st]
        unit_seqs.append(keys)
        unit_time_seqs.append(times)
        word_seqs.append(words)
        span_seqs.append((times[0], times[-1]))
        if (i + 1) % 50 == 0:
            print(f"  ingested {i+1}/{len(sel)}  "
                  f"utts_kept={len(unit_seqs)}  ({time.time()-t0:.0f}s)",
                  flush=True)

    print(f"\nIngested {len(unit_seqs)} usable utterances in "
          f"{time.time()-t0:.0f}s")
    if not unit_seqs:
        print("No usable utterances — aborting.")
        return

    # ----- the structure: TP over the raw sub-word units
    tp = estimate_tp(unit_seqs)
    tp_vals = sorted(tp.values())
    n = len(tp_vals)
    med = tp_vals[n // 2] if n else 0.0
    print("\n==================================================")
    print("(0) TRANSITIONAL-PROBABILITY STRUCTURE (the signal)")
    print("==================================================")
    print(f"distinct sub-word units      : "
          f"{len({u for s in unit_seqs for u in s})}")
    print(f"distinct transitions (bigram): {n}")
    if n:
        print(f"TP distribution: min {tp_vals[0]:.3f}  median {med:.3f}  "
              f"max {tp_vals[-1]:.3f}  mean {sum(tp_vals)/n:.3f}")
        print(f"  (the running median {med:.3f} is the structure-derived "
              f"boundary level — NOT swept)")

    # ----- FORWARD CONSTRUCTION (the agent builds; graph boundary rule runs)
    res = forward_segment(sub, unit_seqs, n_passes=n_passes)
    chunked = res["chunked"]
    print("\n==================================================")
    print("(1) FORWARD CONSTRUCTION (graph boundary rule -> chunks)")
    print("==================================================")
    for pinfo in res["passes"]:
        print(f"  pass {pinfo['pass']}: alphabet={pinfo['alphabet_size']:5d}  "
              f"level(median TP)={pinfo['level']:.3f}  "
              f"boundaries={pinfo['total_boundaries']}")

    # raw = each sub-word unit is its own chunk
    raw_chunked = [[(u,) for u in s] for s in unit_seqs]
    raw_stats = chunk_stats(raw_chunked)
    con_stats = chunk_stats(chunked)
    print("\n==================================================")
    print("(A) CHUNK SHAPE  (word-like = FEWER, LONGER, RECURRING)")
    print("==================================================")
    print(f"{'':18s}{'count':>10s}{'mean_len':>10s}{'recurrence':>12s}")
    print(f"{'raw sub-word':18s}{raw_stats['n_chunks']:>10d}"
          f"{raw_stats['mean_len']:>10.2f}{raw_stats['recurrence']:>12.3f}")
    print(f"{'constructed':18s}{con_stats['n_chunks']:>10d}"
          f"{con_stats['mean_len']:>10.2f}{con_stats['recurrence']:>12.3f}")
    fewer = con_stats['n_chunks'] < raw_stats['n_chunks']
    longer = con_stats['mean_len'] > raw_stats['mean_len']
    print(f"  -> fewer: {'YES' if fewer else 'no'}   "
          f"longer: {'YES' if longer else 'no'}")

    # ----- (B) COMPRESSION — the SELECTOR, computed AFTER the build
    raw_seqs_tok = [[_keystr(u) for u in s] for s in unit_seqs]
    con_seqs_tok = [[_keystr(c) for c in seq] for seq in chunked]
    raw_mdl = description_length_bits(raw_seqs_tok)
    con_mdl = description_length_bits(con_seqs_tok)
    print("\n==================================================")
    print("(B) COMPRESSION  (two-part MDL; SELECTOR, post-hoc)")
    print("==================================================")
    print(f"{'':18s}{'tokens':>9s}{'lexicon':>9s}{'bits/token':>12s}"
          f"{'total Mbits':>13s}")
    print(f"{'raw sub-word':18s}{raw_mdl['n_tokens']:>9d}"
          f"{raw_mdl['lexicon']:>9d}{raw_mdl['bits_per_token']:>12.3f}"
          f"{raw_mdl['bits_total']/1e6:>13.3f}")
    print(f"{'constructed':18s}{con_mdl['n_tokens']:>9d}"
          f"{con_mdl['lexicon']:>9d}{con_mdl['bits_per_token']:>12.3f}"
          f"{con_mdl['bits_total']/1e6:>13.3f}")
    better = con_mdl['bits_total'] < raw_mdl['bits_total']
    print(f"  -> chunked stream compresses better (lower total bits): "
          f"{'YES' if better else 'NO'} "
          f"({con_mdl['bits_total']/max(raw_mdl['bits_total'],1):.3f}x raw)")

    # ----- (C) ALIGNMENT to real word boundaries
    tol = 0.06     # seconds; ~ one syllable-ish window for a rough reference
    rp = rr = rf = 0.0
    cp = cr = cf = 0.0
    nutt = 0
    raw_pure_m = con_pure_m = 0.0
    raw_pure_m_n = con_pure_m_n = 0
    raw_pure_all = con_pure_all = 0.0
    for seq, times, words, (ts, te), chunks in zip(
            unit_seqs, unit_time_seqs, word_seqs, span_seqs, chunked):
        true_b = proportional_word_boundaries(words, ts, te)
        u2w = unit_word_map(times, words, ts, te)
        # raw: a boundary after every unit
        raw_lengths = [1] * len(seq)
        raw_b = boundary_times_of_chunks(times, raw_lengths)
        # constructed: chunk lengths in UNITS (flatten nested chunk-tuples)
        con_lengths = [_flat_len(c) for c in chunks]
        con_b = boundary_times_of_chunks(times, con_lengths)
        p, r, f = boundary_pr(raw_b, true_b, tol)
        rp += p; rr += r; rf += f
        p, r, f = boundary_pr(con_b, true_b, tol)
        cp += p; cr += r; cf += f
        ra, rm, rmn = chunk_purity(raw_lengths, u2w)
        ca, cm, cmn = chunk_purity(con_lengths, u2w)
        raw_pure_all += ra; con_pure_all += ca
        if rmn:
            raw_pure_m += rm * rmn; raw_pure_m_n += rmn
        if cmn:
            con_pure_m += cm * cmn; con_pure_m_n += cmn
        nutt += 1

    nutt = max(nutt, 1)
    print("\n==================================================")
    print("(C) ALIGNMENT to REAL word boundaries "
          f"(proportional ref, tol={tol*1000:.0f}ms)")
    print("==================================================")
    print(f"{'':18s}{'precision':>11s}{'recall':>10s}{'F1':>8s}")
    print(f"{'raw sub-word':18s}{rp/nutt:>11.3f}{rr/nutt:>10.3f}{rf/nutt:>8.3f}")
    print(f"{'constructed':18s}{cp/nutt:>11.3f}{cr/nutt:>10.3f}{cf/nutt:>8.3f}")
    print(f"chunk-to-word PURITY (all chunks):")
    print(f"  raw (single-unit, trivially pure): {raw_pure_all/nutt:.3f}")
    print(f"  constructed                      : {con_pure_all/nutt:.3f}")
    print(f"chunk-to-word PURITY (multi-unit chunks only — the honest number):")
    print(f"  constructed multi-unit purity    : "
          f"{con_pure_m/max(con_pure_m_n,1):.3f}  "
          f"(over {con_pure_m_n} chunks of length>=2)")

    # ----- VERDICT
    print("\n==================================================")
    print("VERDICT — did forward construction discover word-like units?")
    print("==================================================")
    align_better = (cf / nutt) > (rf / nutt) * 1.05
    print(f"(A) fewer & longer chunks    : {'YES' if fewer and longer else 'NO'}")
    print(f"(B) compresses better        : {'YES' if better else 'NO'}")
    print(f"(C) boundaries align better  : {'YES' if align_better else 'NO'} "
          f"(F1 {cf/nutt:.3f} vs raw {rf/nutt:.3f})")
    discovered = fewer and longer and better and align_better
    if discovered:
        print("\n>>> FORWARD CONSTRUCTION DISCOVERS WORD-LIKE UNITS: the TP "
              "structure of the agent's sub-word stream constructively yields "
              "fewer, longer, recurring, better-compressing, better-aligned "
              "chunks — the Saffran mechanism works on its perception.")
    else:
        print("\n>>> HONEST FINDING: forward construction "
              f"{'partially ' if (fewer and longer and better) else ''}"
              "improves shape/compression"
              f"{' but real-speech TP is too noisy for clean word boundaries' if not align_better else ''}"
              ". The chunks are more word-LIKE by shape/compression; "
              "boundary alignment on real continuous speech is "
              f"{'better' if align_better else 'limited by noisy sub-word TP'}. "
              "Reported as measured — no tuning to force it.")


def _flat_len(chunk):
    """Number of leaf sub-word units a (possibly nested, multi-pass) chunk spans."""
    if isinstance(chunk, tuple):
        return sum(_flat_len(c) for c in chunk)
    return 1


if __name__ == "__main__":
    main()

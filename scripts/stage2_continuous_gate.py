"""STAGE 2 (CONTINUOUS SPEECH) — segmentation-coherence / self-tuning gate on
TRANSITION-PROBABILITY TROUGHS, fed by the voicing-edge sonority landmark.

THE LEVER (per commits f98e7206 / b699d215 / 5ff04a2e, docs/stage2_edges_gate.md):
four isolated-digit segmentation gates (energy valleys -> periodicity valleys ->
voicing edges, across 8 kHz + clean 16 kHz) ALL failed the SAME structural way — a
monotone exponential decay of the grain curve, no self-tuning plateau, and a
speaker-dependent grain (lucas coarse, george fine). The honest diagnosis: the
sonority-segmentation cue is NOT cleanly present in an isolated single digit — a
short isolated word has no STREAM, hence no transition-probability TROUGH to carve
at. The cue that DOES self-tune lives in CONTINUOUS SPEECH, where the boundary
signal is the TP-trough across a stream of syllables/words (Saffran-style
statistical learning; ozma_learns_from_sentences: a recurring lexicon condenses
recurrence 0.98, transition info-gain 1.21 bits, held-out next-unit prediction
1.52x the frequency baseline and COLLAPSES under shuffle — structure is in the
ORDER). The voicing-edge landmark (d'=6.0 TFS voicing onset/offset hysteresis,
commit b699d215) earned its place as the TIGHTEST cross-speaker grain of the three
isolated-digit operations; it is retired from the isolated-digit gate as a
self-tuning segmenter but kept here as the per-utterance SONORITY FEATURE that
co-confirms boundary candidates.

WHAT THIS SCRIPT DOES (a world-adapter MEASUREMENT script — no agent reasoning here;
CortexLoop / scripts/solve_for_n.py UNTOUCHED; no Rust touched — the native TFS
chain is already bound, the TP-trough segmenter and the landmark co-gate are thin
mechanical transducers over the agent's OUTPUT stream + the native voicing track):

  CORPUS + UNIT STREAM (reused VERBATIM from scripts/sentence_learning.py):
    LibriSpeech dev-clean, ingested through STTPipeline.ingest (the agent's
    perception). Each utterance -> an ORDERED sub-word unit stream = the list of
    AcousticSign NodeID `.value` keys (the pipeline reuses the SAME sign id when a
    sound recurs via DTW merge, so identity = recurrence). This is the exact stream
    sentence_learning.py computes its TP / info-gain over.

  TP-TROUGH SEGMENTER (the segmentation OPERATION, fed by the landmark):
    Forward transition probability P(next | cur) is estimated over the WHOLE unit
    stream (the same bigram statistics sentence_learning.py uses). Within an
    utterance, a BOUNDARY CANDIDATE is a local TROUGH of the forward TP of the
    SUCCESSOR unit: high within-chunk predictability, a DROP at a boundary
    (a -> b with LOW P(b|a) flanked by HIGHER P on both sides = the Saffran cue).
    The trough DEPTH = how far the TP dips below its local neighbours; a trough is
    accepted as a cut when depth >= a swept threshold `theta`. The voicing-edge
    landmark CO-GATES: a per-utterance voicing onset/offset landmark near a TP
    trough SHARPENS it (the depth is boosted at landmark-aligned positions), so the
    sonority skeleton and the statistical-trough cue must AGREE for the strongest
    cuts. The grain = number of segments per utterance.

  THE GATE (STRUCTURAL, NOT a held-out accuracy; READ THE NUMBERS, not the boolean):
    (i)   SELF-TUNING: sweep theta; does the grain curve flatten into a STABLE
          plateau (a stable operating regime / grain), UNLIKE the isolated-digit
          monotone-decay failure? (the SAME corrected interior-shelf detector the
          agent fixed for the isolated-digit gates, reused VERBATIM).
    (ii)  CONDENSATION: do the resulting SEGMENTS form a recurring lexicon —
          segment-unit-sequences recur across utterances (recurrence, compare the
          0.98 baseline), the lexicon condensing (distinct << total)?
    (iii) LINGUISTIC ALIGNMENT: does the segment count track the transcript WORD
          count better than chance, AND does the TP-trough structure COLLAPSE under
          a frequency-preserving SHUFFLE of the stream (proving the boundaries are
          in the ORDER, not the marginal unit frequency)? This shuffle control is
          the honest do-contrast — the held-out word count is a SANITY scale, never
          banked as the readiness gate.

  Donkey-clean: native gammatone_band -> band_autocorr -> summary_autocorrelogram
  -> periodicity_track for the voicing landmark; bigram TP over the agent's own
  sign-id output for the troughs. No net, no .fit, no gradient, no loss, no
  recognition score. The theta sweep FINDS the operating regime; it is NOT an
  accuracy fit.

Run: PYTHONUNBUFFERED=1 python -m scripts.stage2_continuous_gate [n_utts] [n_spk]
"""

from __future__ import annotations

import math
import os
import random
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import substrate_rs._native as _n
from domains.stt_pipeline import STTPipeline, STTParams

DATA_DIR = "/tmp/LibriSpeech/dev-clean"
_FN_RE = re.compile(r"(\d+)-(\d+)-(\d+)\.flac")

FS = 8000  # the pipeline's rate

# --- voicing-edge landmark: the native TFS periodicity chain (VERBATIM from -----
# scripts/stage2_edges_gate.py / the validated T4 chain, commit 90b799c9). The d'=6.0
# voiced<->unvoiced axis. The landmark co-gates the TP troughs as the per-utterance
# sonority feature.
FRAME_MS = 32.0
HOP_MS = 12.0
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)     # 256 samples
TFS_HOP = int(FS * HOP_MS / 1000)       # 96 samples
TFS_MINLAG, TFS_MAXLAG = 25, 100
TFS_NLAGS = TFS_MAXLAG + 1

# TP-trough depth sweep — the segmenter's ONE free parameter, swept across its whole
# admissible range. theta=0 -> cut at EVERY local TP minimum (max over-segmentation);
# large theta -> only the deepest statistical troughs cut (coarsest grain). We LOOK
# FOR a self-tuning plateau, exactly as the isolated-digit gates looked for one over
# the depth_threshold / hysteresis band.
THETA_SWEEP = [round(0.02 * k, 3) for k in range(0, 40)]   # 0.00 .. 0.78

# voicing-edge hysteresis band — FIXED at the diagnostic operating point the
# isolated-digit edges run found tightest (h*=0.26, docs/stage2_edges_gate.md). The
# landmark is a CO-GATE feature here, not the swept knob; theta is the swept knob.
EDGE_HYST = 0.26
# how strongly a landmark-aligned trough is sharpened (additive depth boost). A
# landmark within LANDMARK_RADIUS units of a trough confirms it; structural, fixed.
LANDMARK_BOOST = 0.10
LANDMARK_RADIUS = 1


# ---------------------------------------------------------------------------
# corpus + unit stream (reused from sentence_learning.py)
# ---------------------------------------------------------------------------
def gather_pairs():
    out = []
    for root, _, names in os.walk(DATA_DIR):
        trans = {}
        for fn in names:
            if not fn.endswith(".trans.txt"):
                continue
            with open(os.path.join(root, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        trans[parts[0]] = parts[1]
        for fn in names:
            m = _FN_RE.match(fn)
            if not m:
                continue
            sp, ch, ut = m.groups()
            utt_id = f"{sp}-{ch}-{ut}"
            if utt_id in trans:
                out.append((os.path.join(root, fn), sp, ch, ut, trans[utt_id]))
    out.sort()
    return out


def load_flac_8k(path):
    import av
    c = av.open(path)
    s = c.streams.audio[0]
    arr = np.concatenate([
        f.to_ndarray().flatten().astype(np.float32) for f in c.decode(s)
    ])
    rate = s.rate
    c.close()
    peak = max(float(np.abs(arr).max()), 1.0)
    arr = (arr / peak * 0.7).astype(np.float32)
    if rate == 16000:
        try:
            from scipy.signal import decimate
            arr = decimate(arr, 2).astype(np.float32)
        except Exception:
            arr = arr[::2].astype(np.float32)
    elif rate != 8000:
        factor = max(1, round(rate / 8000))
        arr = arr[::factor].astype(np.float32)
    return np.ascontiguousarray(arr), 8000


# ---------------------------------------------------------------------------
# voicing-edge landmarks (VERBATIM hysteresis state machine over the native track)
# ---------------------------------------------------------------------------
def periodicity_envelope(x):
    """The graded TFS periodicity/voicing track — native gammatone_band ->
    band_autocorr -> summary_autocorrelogram -> periodicity_track. Per-frame
    voicing strength in [0,1]. VERBATIM from scripts/stage2_edges_gate.py."""
    s = np.asarray(x, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None
    s_list = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)
        ac = _n.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None
    sacf = _n.summary_autocorrelogram(band_acs, TFS_NLAGS)
    if not sacf:
        return None
    pt = _n.periodicity_track(sacf, TFS_NLAGS, TFS_MINLAG, TFS_MAXLAG)
    if not pt:
        return None
    strengths = np.array(pt[0::2], dtype=np.float32)
    if len(strengths) < 8:
        return None
    return strengths


def voicing_edge_frames(env, hyst=EDGE_HYST):
    """Voicing onset/offset landmark FRAME indices via the hysteresis state machine
    (VERBATIM rule from scripts/stage2_edges_gate.py:edge_count, returning the
    landmark POSITIONS rather than just the count). Returns a list of periodicity-
    frame indices where a voicing transition occurs."""
    if env is None or len(env) < 3:
        return []
    p = np.asarray(env, dtype=np.float64)
    level = float(np.median(p))
    thr_hi = level + hyst / 2.0
    thr_lo = level - hyst / 2.0
    voiced = p[0] >= level
    frames = []
    for i in range(1, len(p)):
        v = p[i]
        if not voiced:
            if v >= thr_hi:
                voiced = True
                frames.append(i)
        else:
            if v <= thr_lo:
                voiced = False
                frames.append(i)
    return frames


# ---------------------------------------------------------------------------
# TP-trough segmenter
# ---------------------------------------------------------------------------
def build_forward_tp(sequences):
    """Forward transition probability P(next | cur) estimated over the whole unit
    stream (the same bigram statistics sentence_learning.py uses). Returns a dict
    cur -> {next -> P}."""
    bigrams = {}
    for seq in sequences:
        for a, b in zip(seq, seq[1:]):
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    tp = {}
    for a, nexts in bigrams.items():
        tot = sum(nexts.values())
        tp[a] = {b: c / tot for b, c in nexts.items()}
    return tp


def tp_curve(seq, tp):
    """Per-position forward TP: at position i, the probability P(seq[i] | seq[i-1]).
    High = predictable continuation (within a chunk); a LOCAL MINIMUM = a transition
    the stream did not expect = a Saffran boundary candidate. Position 0 has no
    predecessor -> set to a high value (utterance start is a hard boundary anyway)."""
    vals = [1.0]
    for i in range(1, len(seq)):
        a, b = seq[i - 1], seq[i]
        vals.append(tp.get(a, {}).get(b, 0.0))
    return vals


def landmark_units(seq_len, edge_frames, n_frames):
    """Map voicing-landmark FRAME indices onto UNIT-stream positions. The unit
    stream and the periodicity-frame grid are different clocks; map proportionally
    (the sign stream is monotone in time, so a landmark at frame f lands near unit
    position round(f / n_frames * seq_len)). Returns a set of unit positions that
    carry a voicing landmark = the per-utterance sonority feature."""
    if seq_len <= 0 or n_frames <= 0:
        return set()
    pos = set()
    for f in edge_frames:
        u = int(round(f / max(n_frames, 1) * seq_len))
        u = max(0, min(seq_len - 1, u))
        pos.add(u)
    return pos


def segment_by_troughs(seq, tpc, landmark_pos, theta):
    """Cut the unit stream at forward-TP TROUGHS whose depth >= theta. A trough at
    position i: tpc[i] is a local minimum (<= both neighbours) and the DEPTH =
    min(neighbour) - tpc[i] (how far the TP dips below the higher of its flanks).
    The voicing landmark CO-GATES: a landmark within LANDMARK_RADIUS of i adds
    LANDMARK_BOOST to the effective depth (sonority + statistics must AGREE for the
    strongest cuts). Returns the list of segments (each a tuple of unit keys)."""
    n = len(seq)
    if n < 2:
        return [tuple(seq)] if seq else []
    cuts = set()
    for i in range(1, n - 1):
        left, here, right = tpc[i - 1], tpc[i], tpc[i + 1]
        if here <= left and here <= right:
            depth = min(left, right) - here
            # voicing-landmark co-gate: sharpen landmark-aligned troughs
            if any((i + d) in landmark_pos
                   for d in range(-LANDMARK_RADIUS, LANDMARK_RADIUS + 1)):
                depth += LANDMARK_BOOST
            if depth >= theta:
                cuts.add(i)        # cut BEFORE position i (boundary at the dip)
    segs = []
    start = 0
    for i in range(1, n):
        if i in cuts:
            segs.append(tuple(seq[start:i]))
            start = i
    segs.append(tuple(seq[start:]))
    return [s for s in segs if s]


# ---------------------------------------------------------------------------
# the structural detectors (interior-shelf VERBATIM from the isolated-digit gate)
# ---------------------------------------------------------------------------
def detect_plateau(xs, grain):
    """The corrected interior-shelf plateau detector (VERBATIM logic from
    scripts/stage2_edges_gate.py): a relative-flat shelf at a non-trivial grain,
    bracketed by steeper descent — an INTERIOR local-derivative minimum, NOT the flat
    top or collapsed tail of a monotone decay. Returns (plateau_lo, plateau_hi,
    best_len, rel_slopes, median_slope, REL_TOL)."""
    deriv = []
    for i in range(1, len(xs)):
        dg = grain[xs[i]] - grain[xs[i - 1]]
        deriv.append((xs[i], dg))
    rel_slopes = [abs(dg) / max(grain[xs[i + 1]], 1e-6)
                  for i, (_, dg) in enumerate(deriv)]
    median_slope = float(np.median(rel_slopes)) if rel_slopes else 0.0
    # REL_TOL = flatter than half the median slope (the isolated-digit gate's rule),
    # but floored at a small absolute value: a genuinely FLAT plateau drives the
    # median slope toward 0, which would make 0.5*median an unreachable bar and
    # FALSELY report "no shelf" on a real shelf. The floor (0.01 = 1% per step)
    # keeps a monotone decay disqualified (its slope is non-zero everywhere) while
    # letting a true flat shelf register. Honest detector fix, not a gate loosening.
    REL_TOL = max(0.01, min(0.04, 0.5 * median_slope))
    GRAIN_FLOOR = 1.5            # a segment grain of >=1.5 segs/utt is non-trivial
    GRAIN_CEIL = 60.0           # continuous utterances are long -> many segments
    EDGE_GUARD = 3
    stable_flags = []
    for i, (_, dg) in enumerate(deriv):
        gi = grain[xs[i + 1]]
        rel = abs(dg) / max(gi, 1e-6)
        interior = EDGE_GUARD <= (i + 1) <= (len(xs) - 1 - EDGE_GUARD)
        stable_flags.append(rel < REL_TOL and GRAIN_FLOOR <= gi <= GRAIN_CEIL
                            and interior)
    best_run = (0, -1, -1)
    i = 0
    while i < len(stable_flags):
        if stable_flags[i]:
            j = i
            while j < len(stable_flags) and stable_flags[j]:
                j += 1
            length = j - i + 1
            if length > best_run[0]:
                best_run = (length, i + 1, j + 1)
            i = j + 1
        else:
            i += 1
    plo = phi = None
    if best_run[0] > 0:
        plo = xs[best_run[1]]
        phi = xs[best_run[2]]
    return plo, phi, best_run[0], rel_slopes, median_slope, REL_TOL


def segment_recurrence(all_segments):
    """Condensation: do the SEGMENTS form a recurring lexicon? Returns (recurrence,
    distinct, total). recurrence = fraction of segment tokens that repeat an
    already-seen segment-unit-sequence (compare the 0.98 unit-level baseline)."""
    seen = set()
    total = repeat = 0
    for seg in all_segments:
        total += 1
        if seg in seen:
            repeat += 1
        else:
            seen.add(seg)
    rec = repeat / max(total, 1)
    return rec, len(seen), total


# ---------------------------------------------------------------------------
def main():
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    print("=" * 74)
    print("STAGE 2 (CONTINUOUS SPEECH) — TP-TROUGH SEGMENTATION + VOICING-EDGE")
    print("  LANDMARK — segmentation-coherence / self-tuning gate (STRUCTURAL).")
    print("  The lever the four isolated-digit gates named: the boundary cue is a")
    print("  TRANSITION-PROBABILITY TROUGH across a STREAM, not a valley in one word.")
    print("  NOT a held-out recognition accuracy. READ THE NUMBERS.")
    print("=" * 74)

    pairs = gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    print(f"LibriSpeech dev-clean: {len(pairs)} utterances, "
          f"{len(speakers)} speakers")
    chosen = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen]
    random.shuffle(sel)
    sel = sel[:n_utts]
    print(f"Using {len(sel)} utterances from {n_speakers} speakers {chosen}\n")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)

    # --- ingest: ordered unit stream + voicing-edge landmark frames per utt -------
    sequences = []        # [unit_key, ...] per utterance
    edge_frames_l = []    # voicing-landmark frame indices per utterance
    n_frames_l = []       # periodicity-frame count per utterance
    word_counts = []      # transcript word count per utterance (scale sanity)
    spk_l = []
    seen_units = set()
    tot_tok = rep_tok = 0
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        samples, _ = load_flac_8k(path)
        try:
            signs = pipe.ingest(sub, samples)
        except Exception as e:
            print(f"  FAIL ingest {path}: {e}", flush=True)
            continue
        sub.tick(50000)
        seq = []
        for s in signs:
            v = getattr(s, "value", None)
            key = v if v is not None else repr(s)
            seq.append(key)
            tot_tok += 1
            if key in seen_units:
                rep_tok += 1
            else:
                seen_units.add(key)
        if len(seq) < 2:
            continue
        env = periodicity_envelope(samples)
        ef = voicing_edge_frames(env) if env is not None else []
        nf = len(env) if env is not None else 0
        sequences.append(seq)
        edge_frames_l.append(ef)
        n_frames_l.append(nf)
        word_counts.append(len(transcript.split()))
        spk_l.append(sp)
        if (i + 1) % 50 == 0:
            print(f"  ingested {i+1}/{len(sel)}  units_seen={len(seen_units)}  "
                  f"tokens={tot_tok}  unit-recurrence={rep_tok/max(tot_tok,1):.3f}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    n_utt = len(sequences)
    unit_recurrence = rep_tok / max(tot_tok, 1)
    print(f"\nUTTERANCES with a usable stream: {n_utt}")
    print(f"unit-stream tokens: {tot_tok}   distinct units: {len(seen_units)}   "
          f"unit-level recurrence: {unit_recurrence:.3f}")
    print(f"  (this is the STREAM the isolated digit cannot provide; "
          f"sentence_learning baseline unit recurrence ~0.98)\n")

    if n_utt < 6:
        print("!! too few utterances to run the gate")
        return

    # --- forward TP over the stream + per-utterance trough curves -----------------
    tp = build_forward_tp(sequences)
    tpcs = [tp_curve(seq, tp) for seq in sequences]
    landmark_l = [landmark_units(len(sequences[k]), edge_frames_l[k], n_frames_l[k])
                  for k in range(n_utt)]

    # --- (A) GRAIN vs theta (mean segments/utterance) -----------------------------
    print("--- (A) GRAIN vs TP-trough depth theta (mean segments/utterance) ---")
    grain = {}
    seg_by_theta = {}
    for th in THETA_SWEEP:
        segs_all = []
        counts = []
        for k in range(n_utt):
            s = segment_by_troughs(sequences[k], tpcs[k], landmark_l[k], th)
            segs_all.append(s)
            counts.append(len(s))
        grain[th] = float(np.mean(counts)) if counts else 0.0
        seg_by_theta[th] = segs_all
    for th in THETA_SWEEP:
        bar = "#" * int(round(grain[th]))
        print(f"  theta {th:<5}  grain {grain[th]:6.3f}  {bar}")

    # --- (B) SELF-TUNING PLATEAU (interior-shelf detector, VERBATIM) ---------------
    print("\n--- (B) SELF-TUNING PLATEAU (relative-flat shelf at a non-trivial grain) ---")
    plo, phi, best_len, rel_slopes, median_slope, REL_TOL = detect_plateau(
        THETA_SWEEP, grain)
    print(f"  per-step |Δgrain|/grain over the whole sweep: "
          f"min {min(rel_slopes):.3f}  median {median_slope:.3f}  "
          f"max {max(rel_slopes):.3f}")
    print(f"  (a SHELF needs this near 0 over a band, bracketed by STEEPER descent "
          f"on both sides — an INTERIOR local-derivative minimum, NOT the flat top\n"
          f"   or collapsed tail of a monotone decay. The isolated-digit gates had "
          f"a CONSTANT ~8%/step slope = pure exp decay = NO shelf.)")
    if plo is not None:
        pg = np.mean([grain[d] for d in THETA_SWEEP if plo <= d <= phi])
        print(f"  longest stable run: theta [{plo:.3f} .. {phi:.3f}]  "
              f"({best_len} steps)")
        print(f"  plateau mean grain : {pg:.3f} segments/utterance (stable)")
        print(f"  |Δgrain|/grain in plateau: < {REL_TOL:.4f} per step (relative-flat)")
    else:
        print("  NO stable, non-trivial plateau found — the TP-trough segmenter "
              "does not self-tune on this stream.")

    # operating point
    if plo is not None:
        th_star = round((plo + phi) / 2.0, 3)
        th_star = min(THETA_SWEEP, key=lambda d: abs(d - th_star))
        print(f"\n  operating point theta* = {th_star} (plateau centre)")
    else:
        # diagnostic: the theta whose grain is closest to the transcript word scale
        target = float(np.mean(word_counts)) if word_counts else 8.0
        th_star = min(THETA_SWEEP, key=lambda d: abs(grain[d] - target))
        print(f"\n  NO plateau — diagnostic operating point theta* = {th_star} "
              f"(grain closest to mean word count {target:.1f}; NOT self-tuned)")

    # --- (C) CONDENSATION — do the segments form a recurring lexicon? --------------
    print("\n--- (C) CONDENSATION — recurring SEGMENT lexicon at theta* ---")
    segs_star = [seg for utt in seg_by_theta[th_star] for seg in utt]
    rec, distinct, total = segment_recurrence(segs_star)
    # also single-unit vs multi-unit segments (are we finding real chunks?)
    multi = sum(1 for s in segs_star if len(s) >= 2)
    print(f"  segments at theta*          : {total}  (distinct {distinct})")
    print(f"  segment-lexicon recurrence  : {rec:.3f} "
          f"(fraction of segments repeating an already-seen segment)")
    print(f"  multi-unit segments         : {multi}/{total} = "
          f"{multi/max(total,1):.3f} (a real chunk has >=2 units)")
    print(f"  mean segment length (units) : "
          f"{np.mean([len(s) for s in segs_star]):.2f}")
    print(f"  (unit-level recurrence was {unit_recurrence:.3f}; the SEGMENT lexicon "
          f"condenses if recurrence stays high while distinct << total)")

    # --- (D) LINGUISTIC ALIGNMENT + SHUFFLE CONTROL (the honest do-contrast) -------
    print("\n--- (D) LINGUISTIC ALIGNMENT + SHUFFLE CONTROL ---")
    seg_counts = [len(u) for u in seg_by_theta[th_star]]
    wc = np.array(word_counts, dtype=float)
    sc = np.array(seg_counts, dtype=float)
    if np.std(wc) > 0 and np.std(sc) > 0:
        word_corr = float(np.corrcoef(wc, sc)[0, 1])
    else:
        word_corr = float("nan")
    print(f"  segments/utt vs transcript WORDS/utt corr : {word_corr:+.3f}  "
          f"(scale sanity, NOT the gate)")
    print(f"  mean segments/utt {np.mean(sc):.2f}  vs  mean words/utt "
          f"{np.mean(wc):.2f}")

    # SHUFFLE: pool all unit tokens, shuffle (kills order, keeps unit frequency),
    # re-chunk into same-length pseudo-utterances, rebuild TP, re-segment at theta*.
    # If the troughs are real (in the ORDER), the segment structure must COLLAPSE
    # toward trivial here. This is the do-contrast, NOT a held-out accuracy.
    all_tokens = [t for seq in sequences for t in seq]
    lengths = [len(seq) for seq in sequences]
    random.shuffle(all_tokens)
    shuf_seqs = []
    idx = 0
    for L in lengths:
        shuf_seqs.append(all_tokens[idx:idx + L])
        idx += L
    tp_sh = build_forward_tp(shuf_seqs)
    tpcs_sh = [tp_curve(seq, tp_sh) for seq in shuf_seqs]
    # no landmark co-gate in the shuffle (the audio<->unit alignment is destroyed);
    # this isolates the TP-trough contribution to the order.
    grain_sh = {}
    for th in THETA_SWEEP:
        cnts = [len(segment_by_troughs(shuf_seqs[k], tpcs_sh[k], set(), th))
                for k in range(len(shuf_seqs))]
        grain_sh[th] = float(np.mean(cnts)) if cnts else 0.0
    plo_sh, phi_sh, best_len_sh, rel_sh, med_sh, _ = detect_plateau(
        THETA_SWEEP, grain_sh)
    # real (order) segment structure vs shuffled, at the SAME theta*
    real_grain_star = grain[th_star]
    # recompute real without the landmark co-gate too, for a clean order-only contrast
    grain_noland = {}
    for th in [th_star]:
        cnts = [len(segment_by_troughs(sequences[k], tpcs[k], set(), th))
                for k in range(n_utt)]
        grain_noland[th] = float(np.mean(cnts))
    real_noland = grain_noland[th_star]
    shuf_grain_star = grain_sh[th_star]
    segs_sh_star = [segment_by_troughs(shuf_seqs[k], tpcs_sh[k], set(), th_star)
                    for k in range(len(shuf_seqs))]
    segs_sh_flat = [s for u in segs_sh_star for s in u]
    rec_sh, distinct_sh, total_sh = segment_recurrence(segs_sh_flat)
    print(f"\n  REAL ORDER (theta*={th_star}):")
    print(f"    grain (with landmark co-gate) : {real_grain_star:.3f} segs/utt")
    print(f"    grain (order-only, no landmark): {real_noland:.3f} segs/utt")
    print(f"    segment recurrence            : {rec:.3f}")
    print(f"  SHUFFLED (order destroyed, unit frequency preserved):")
    print(f"    grain                          : {shuf_grain_star:.3f} segs/utt")
    print(f"    segment recurrence             : {rec_sh:.3f}")
    print(f"    self-tuning plateau?           : "
          f"{'YES' if (plo_sh is not None and best_len_sh >= 3) else 'NO'}")
    # the order-structure signal: real troughs should produce a DIFFERENT (lower,
    # quantized) grain than shuffle, and the real plateau should not survive shuffle.
    collapses = (plo is not None and (plo_sh is None or best_len_sh < best_len)) \
        or (abs(real_noland - shuf_grain_star) / max(shuf_grain_star, 1e-6) > 0.10)
    print(f"\n  TP-trough structure is in the ORDER (collapses under shuffle): "
          f"{'YES' if collapses else 'NO'}")
    print(f"    (real order-only grain {real_noland:.3f} vs shuffled "
          f"{shuf_grain_star:.3f}; real plateau {best_len} steps vs shuffled "
          f"{best_len_sh} steps)")

    # --- VERDICT ------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("=== READINESS GATE — TP-TROUGH SEGMENTATION on CONTINUOUS SPEECH "
          "(structural) ===")
    has_plateau = plo is not None and best_len >= 3
    nontrivial = plo is not None and 1.5 <= np.mean(
        [grain[d] for d in THETA_SWEEP if plo <= d <= phi]) <= 60.0
    condenses = rec > 0.05 and distinct < total
    in_order = collapses
    print(f"  (i)   SELF-TUNES (stable grain PLATEAU exists)      : {has_plateau}"
          + (f"  [theta {plo:.2f}..{phi:.2f}, {best_len} steps]"
             if plo is not None else "  [pure monotone decay — like isolated digits]"))
    print(f"        PLATEAU grain non-trivial                    : {nontrivial}")
    print(f"  (ii)  CONDENSES (recurring segment lexicon)        : {condenses}"
          f"  [recurrence {rec:.3f}, distinct {distinct} < total {total}]")
    print(f"  (iii) BOUNDARIES in the ORDER (collapse on shuffle): {in_order}")
    print(f"        word-scale sanity (segs~words corr)          : "
          f"{word_corr:+.3f}")
    print("  " + "-" * 60)
    fires = has_plateau and nontrivial and condenses and in_order
    print(f"  >>> STAGE-2 TP-TROUGH SEGMENTER SELF-TUNES TO A STABLE, COHERENT "
          f"GRAIN: {fires}")
    print("=" * 74)
    print("===MARKER_STAGE2_CONTINUOUS_GATE_COMPLETE===")


if __name__ == "__main__":
    main()

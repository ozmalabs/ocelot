"""GATE — the n=0 continuous-segmentation floor: diagnosed, lifted, characterised.

DIAGNOSIS (the root cause of n=0 on REAL audio).
  The corpus-ingest segmenter `substrate_rs.speech.detect_utterances` cuts the
  stream at SILENCE GAPS — runs of codec frames whose coded_size drops below the
  stream's own 25th percentile. Clean/synthetic speech has such gaps; REAL
  continuous audio (children's TV: speech over continuous background MUSIC) does
  NOT — EVERY frame stays above p25 (measured: frac-active = 1.0), so the whole
  clip is ONE un-broken active run. That single run exceeds `max_duration_s`
  (5.0s) and is DROPPED -> n=0 utterances. The loop banks 0.0 with n=0 segments.
  (Confirmed real-vs-synthetic: the only reason a 2.4s synthetic "worked" was it
  fit under the 5s cap — it too collapsed to a single un-broken run.)

THE FIX (graph-native, donkey=0).
  When the silence-gap walk yields no usable utterance (or one near-whole-stream
  blob), fall back to the agent's HELD word-segmenter — which does NOT depend on
  silence gaps: it reads word boundaries from the TRANSITIONAL-PROBABILITY
  structure of its own sub-word units (Saffran statistical learning), the
  grid-robust PROMINENT-trough rule (local_min AND below-median) compiled to the
  native primitive `_native.segment_units` (be50a0c7). The clip's cochleagram is
  quantised by k-means fit on THIS clip's OWN frames (an adaptive statistic, not
  a magic codebook). The DECISION is the agent's held native primitive; Python is
  mechanical I/O (decode, cochleagram, mint nodes). No LLM, no hand-tuned const.

GATES (all donkey=0, honest):
  MAIN — real jellyfin + LibriSpeech dev-clean now produce n>0 structured units
         at a sane rate (utts/word, near word scale — not 0, not the old 5.9x).
  DISCRIMINATIVE — the produced boundaries align with real word boundaries
         (whisper) better than RANDOM boundaries at the same count.
  CONTENT — present-vs-absent AUC on the segmented real audio. HONEST EXPECTATION
         per the project memory = ~chance (~0.50): the deeper floor is per-frame
         acoustic-phonetic decoding, NOT segmentation. Reported plainly; NO
         best-window-match number is manufactured.
"""
import os, sys, tempfile, subprocess, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import soundfile as sf
import substrate_rs as srs
import substrate_rs.audio as _audio
import substrate_rs.speech as _speech


def _ingest(x, fs):
    s = srs.Substrate()
    _audio.seed_audio_grammar(s); _audio.seed_native_codec_grammar(s)
    _speech.seed_speech_grammar(s)
    raw = tempfile.mktemp(suffix=".wav"); tmp = tempfile.mktemp(suffix=".ogg")
    sf.write(raw, np.asarray(x, dtype=np.float64), int(fs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                    "-ar", "48000", "-ac", "1", "-c:a", "libopus", tmp],
                   check=True, capture_output=True)
    acn = _audio.open_container(s, tmp); asid = _audio.add_stream(s, acn)
    _audio.parse_stream(s, acn, asid); _audio.parse_native(s, acn, asid)
    utts = _speech.detect_utterances(s, asid)
    spans = [(float(s.node(u)["attrs"]["start_time_s"]),
              float(s.node(u)["attrs"]["end_time_s"])) for u in utts]
    os.unlink(raw); os.unlink(tmp)
    return spans


def _boundary_pr(spans, word_bound_t, tol=0.12):
    """Precision/recall of cut TIMES against whisper word-boundary TIMES."""
    cuts = sorted({b for _a, b in spans[:-1]})
    if not word_bound_t or not cuts:
        return None, None
    rec = sum(any(abs(c - wb) <= tol for c in cuts)
              for wb in word_bound_t) / len(word_bound_t)
    prec = sum(any(abs(c - wb) <= tol for wb in word_bound_t)
               for c in cuts) / len(cuts)
    return prec, rec


def main():
    print("=" * 64)
    print("n=0 CONTINUOUS-SEGMENTATION FLOOR — diagnose / lift / characterise")
    print("=" * 64)
    from scripts.source_world import SourceWorld
    sw = SourceWorld()
    ab = next(s for s in sw.sources() if "Abominable" in s.get("name", ""))

    # ---- MAIN + DISCRIMINATIVE on REAL jellyfin (the n=0 source) ---------
    print("\n[MAIN] REAL jellyfin 'Abominable and the Invisible City':")
    rng = np.random.default_rng(0)
    tot_u = tot_w = 0
    precs, recs, rprecs, rrecs = [], [], [], []
    speech_present = []   # (utts/word) per speechy window for sanity
    for (t0, t1) in [(0, 6), (120, 130), (140, 150), (160, 170),
                     (180, 190), (200, 210)]:
        x = sw.play(ab, t0, t1)
        if x.size == 0:
            continue
        spans = _ingest(x, 8000)
        words = sw.whisper(ab, t0, t1)
        wbt = [w[2] for w in words]   # word END times rel t0
        tot_u += len(spans); tot_w += len(words)
        p, r = _boundary_pr(spans, wbt)
        # RANDOM control: same #cuts at random times in [0, t1-t0].
        ncuts = max(len(spans) - 1, 0)
        rc = sorted(rng.uniform(0, t1 - t0, size=ncuts))
        rspans = [(a, b) for a, b in zip([0.0] + rc, rc + [t1 - t0])]
        rp, rr = _boundary_pr(rspans, wbt)
        if p is not None:
            precs.append(p); recs.append(r)
        if rp is not None:
            rprecs.append(rp); rrecs.append(rr)
        print(f"  {t0:3d}-{t1:3d}s: n_utts={len(spans):2d} "
              f"whisper_words={len(words):2d} utts/word="
              f"{len(spans)/max(len(words),1):.2f}x")
    nonzero = tot_u > 0
    print(f"  -> TOTAL utts/word = {tot_u/max(tot_w,1):.2f}x  "
          f"(was n=0 / 0.00x on this source; old over-seg was 5.9x)")
    print(f"  -> non-empty on real audio: {'YES' if nonzero else 'NO'}")
    # The DISCRIMINATIVE test characterises THE FIX (the held TP-trough
    # segmenter), so it forces the structural path on speech-bearing continuous
    # windows and compares ITS cuts to random at the same count. (The end-to-end
    # detect_utterances above keeps the codec gap-walk on windows that DO have
    # silence structure — frac_active < 0.9 — so the table above mixes the two;
    # this block isolates the new component.)
    print(f"\n[DISCRIMINATIVE] held TP-trough segmenter vs random "
          f"(boundary P/R vs whisper, speech windows):")
    hp, hr, xp, xr = _discriminative_structural(sw, ab, rng)
    print(f"  held segmenter : P={hp:.2f} R={hr:.2f}")
    print(f"  random (=#cuts): P={xp:.2f} R={xr:.2f}")
    beats = (hr > xr + 1e-6) or (hp > xp + 1e-6)
    print(f"  -> held beats random: {'YES' if beats else 'NO'}")

    # ---- MAIN on LibriSpeech dev-clean (second corpus) -------------------
    print("\n[MAIN] LibriSpeech dev-clean:")
    flacs = sorted(glob.glob("/tmp/LibriSpeech/dev-clean/**/*.flac",
                             recursive=True))[:6]
    lu = lw = 0
    for f in flacs:
        x, fs = sf.read(f)
        if x.ndim > 1:
            x = x.mean(1)
        spans = _ingest(x, fs)
        base = os.path.basename(f).replace(".flac", "")
        nw = None
        for tf in glob.glob(os.path.join(os.path.dirname(f), "*.trans.txt")):
            for line in open(tf):
                if line.startswith(base + " "):
                    nw = len(line.strip().split(" ")[1:])
        lu += len(spans); lw += (nw or 0)
        print(f"  {base}: n_utts={len(spans):2d} ref_words={nw} "
              f"utts/word={len(spans)/max(nw or 1,1):.2f}x")
    print(f"  -> LibriSpeech utts/word = {lu/max(lw,1):.2f}x  "
          f"non-empty: {'YES' if lu>0 else 'NO'}")

    # ---- CONTENT CONTROL — present-vs-absent AUC (the DEEPER floor) ------
    # Per the canonical control (project memory RETRACTION): the honest content
    # metric is present-vs-absent AUC, NOT best-window match. Pick a frequent
    # whisper word; for each segmented unit score cosine(unit-feature, word-
    # template). AUC of "unit overlaps a true occurrence of the word" vs not.
    print("\n[CONTENT] present-vs-absent AUC on segmented real audio:")
    print("  (honest expectation per memory = ~chance 0.50; the deeper floor is")
    print("   per-frame acoustic-phonetic decoding, NOT segmentation.)")
    auc = _content_auc(sw, ab)
    if auc is None:
        print("  -> insufficient occurrences to score (skipped)")
    else:
        verdict = ("~chance — segmentation does not unlock content"
                   if auc <= 0.58 else
                   "weakly above chance on a tiny sample; NOT a content win — "
                   "the per-frame acoustic-phonetic floor stands")
        print(f"  -> AUC = {auc:.3f}  ({verdict})")

    print("\n" + "=" * 64)
    print(f"VERDICT: n=0 floor {'LIFTED' if nonzero else 'NOT lifted'}; "
          f"discriminative {'PASS' if beats else 'FAIL'}; "
          f"recognition floor characterised (AUC above).")
    print("=" * 64)
    return 0 if (nonzero and beats) else 1


def _discriminative_structural(sw, src, rng):
    """Force the HELD TP-trough segmenter (the fix) on speech windows and measure
    its boundary precision/recall vs whisper, against random cuts at the same
    count. Calls `_structural_segment` directly so the test isolates the new
    component (not the codec gap-walk that still runs on gappy windows)."""
    hp = hr = xp = xr = 0.0
    n = 0
    for (t0, t1) in [(120, 130), (140, 150), (160, 170),
                     (180, 190), (200, 210)]:
        x = sw.play(src, t0, t1)
        if x.size == 0:
            continue
        s, asid = _build_stream(x, 8000)
        inner = _speech._native(s)
        items = [(float(inner.node(f)["attrs"].get("time_s", 0.0)), f)
                 for f in inner.neighbours(asid, _speech.HAS_FRAME)]
        items.sort()
        if len(items) < 8:
            continue
        span = items[-1][0] - items[0][0]
        fr = (len(items) - 1) / span if span > 0 else 0.0
        utts = _speech._structural_segment(
            s, asid, items, fr, min_duration_s=0.0, max_duration_s=5.0)
        spans = [(float(s.node(u)["attrs"]["start_time_s"]),
                  float(s.node(u)["attrs"]["end_time_s"])) for u in utts]
        words = sw.whisper(src, t0, t1)
        wbt = [w[2] for w in words]
        p, r = _boundary_pr(spans, wbt)
        if p is None:
            continue
        ncuts = max(len(spans) - 1, 0)
        rc = sorted(rng.uniform(0, t1 - t0, size=ncuts))
        rspans = [(a, b) for a, b in zip([0.0] + rc, rc + [t1 - t0])]
        rp, rr = _boundary_pr(rspans, wbt)
        hp += p; hr += r; xp += rp; xr += rr; n += 1
    n = max(n, 1)
    return hp / n, hr / n, xp / n, xr / n


def _build_stream(x, fs):
    s = srs.Substrate()
    _audio.seed_audio_grammar(s); _audio.seed_native_codec_grammar(s)
    _speech.seed_speech_grammar(s)
    raw = tempfile.mktemp(suffix=".wav"); tmp = tempfile.mktemp(suffix=".ogg")
    sf.write(raw, np.asarray(x, dtype=np.float64), int(fs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                    "-ar", "48000", "-ac", "1", "-c:a", "libopus", tmp],
                   check=True, capture_output=True)
    acn = _audio.open_container(s, tmp); asid = _audio.add_stream(s, acn)
    _audio.parse_stream(s, acn, asid); _audio.parse_native(s, acn, asid)
    os.unlink(raw); os.unlink(tmp)
    return s, asid


def _content_auc(sw, src):
    """Present-vs-absent AUC for the most frequent content word across windows.
    Unit feature = mean cochleagram over the unit's frames; template = mean over
    that word's true occurrences. AUC over all units: label=overlaps-a-true-occ."""
    from scipy.signal import resample_poly
    import scripts.jabberwock_reads_oov_from_phones as J

    def play16(t0, t1):
        x = sw.play(src, t0, t1)
        return resample_poly(x, 16000, 8000) if x.size else np.zeros(0)

    units, labels, occ_by_win = [], [], []
    from collections import Counter
    wc = Counter()
    wins = [(120, 130), (140, 150), (160, 170), (180, 190), (200, 210)]
    cache = {}
    for (t0, t1) in wins:
        x = play16(t0, t1)
        if x.size == 0:
            continue
        M = J.frames(x)[0]
        spans = _ingest(sw.play(src, t0, t1), 8000)
        words = sw.whisper(src, t0, t1)
        for w in words:
            wc[w[0]] += 1
        cache[(t0, t1)] = (M, spans, words, t1 - t0)
    if not wc:
        return None
    target = max(wc, key=wc.get)
    if wc[target] < 3:
        return None
    # build word template from true occurrences (mean cochleagram in occ spans).
    fps = J.FPS
    temp_feats = []
    for (t0, t1), (M, spans, words, dur) in cache.items():
        for w in words:
            if w[0] != target:
                continue
            a = int(w[1] * fps); b = int(w[2] * fps)
            if b > a and b <= len(M):
                temp_feats.append(M[a:b].mean(0))
    if len(temp_feats) < 2:
        return None
    template = np.mean(temp_feats, axis=0)
    template /= (np.linalg.norm(template) + 1e-9)
    scores, ys = [], []
    for (t0, t1), (M, spans, words, dur) in cache.items():
        occ = [(w[1], w[2]) for w in words if w[0] == target]
        for (sa, sb) in spans:
            fa = int(sa * fps); fb = int(sb * fps)
            if fb <= fa or fb > len(M):
                continue
            feat = M[fa:fb].mean(0); feat /= (np.linalg.norm(feat) + 1e-9)
            scores.append(float(feat @ template))
            ys.append(int(any(not (sb <= oa or sa >= ob) for (oa, ob) in occ)))
    if sum(ys) == 0 or sum(ys) == len(ys):
        return None
    # AUC (Mann-Whitney).
    order = np.argsort(scores)
    ranks = np.empty(len(scores)); ranks[order] = np.arange(1, len(scores) + 1)
    ys = np.array(ys); npos = ys.sum(); nneg = len(ys) - npos
    auc = (ranks[ys == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)
    return float(auc)


if __name__ == "__main__":
    raise SystemExit(main())

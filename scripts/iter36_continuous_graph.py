"""iter36_continuous_graph — apply the SAME enriched recognition GRAPH (iter-34's
20 gammatone channels + FFT-ear + formant-relation + manner/voicing + iter-35's
single-pass AxS node, ALL combined via the variadic Argmax-of-product) to
CONTINUOUS-SPEECH word recognition, where the bottom-up FAILS (coarticulation /
cross-speaker), so the orthogonal cues should become INFORMATIONALLY COMPLEMENTARY.

PART A of iter-36 (docs/agent_loop_iteration36_continuous_and_transfer.md).

NO-DONKEY: this is a WORLD ADAPTER. It slices LibriSpeech utterances into gold-span
WORD clips (faster-whisper forced alignment, the iter-15 gold-span harness) and feeds
them to the EXACT iter-34/35 `build_fold` / `score_fold` machinery as a
`voice_audio = {speaker: [(x, fs, word), ...]}` map — the identical structure the
FSDD digit harness uses, just continuous words instead of isolated digits. The
recognition graph, every cue, the combine-all product, the per-node drop-it, the
shuffle control are all the iter-34/35 code UNCHANGED. The only new code is the
audio-slicing + the shared-vocabulary gating + a cross-speaker same-word CONSISTENCY
metric (the iter-15 DTW NN, reported alongside recognition).

Held-out = held-out SPEAKERS (the real speaker-independent test, where the bottom-up
breaks on cross-speaker variation).

Run: python -m scripts.iter36_continuous_graph [n_speakers] [utts_per_spk]
       [min_exemplars_per_word] [max_vocab]
ENV: AXS=1 to include the AxS node (default 1); set AXS=0 to drop it.
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from scripts.continuous_speech_recognition import words_of  # noqa: F401 (kept for parity)
import scripts.enriched_hvpt_accept as EH
from scripts.iter15_goldspan_gate import gold_spans
from scripts.iter14_segmentation_consistency import full_dtw


# ---------------------------------------------------------------------------
# Build voice_audio = {speaker: [(x, fs, word), ...]} from GOLD word spans.
# Mechanical world-adapter slicing only (no agent reasoning).
# ---------------------------------------------------------------------------

def gather_gold_words(n_spk, utts_per_spk, wmodel, min_dur=0.10):
    """Per speaker, slice gold-span word waveform clips. Returns
    {speaker: [(x_clip, fs, word), ...]}. min_dur drops too-short clips that the
    LPC / A1 cues can't read."""
    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_spk]
    voice_audio = {}
    t0 = time.time()
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        clips = []
        for path, sp, ch, ut in [(p[0], p[1], p[2], p[3]) for p in ps[:utts_per_spk]]:
            try:
                x, fs = SL.load_flac_8k(path)
            except Exception:
                continue
            try:
                gs = gold_spans(wmodel, path)
            except Exception:
                gs = []
            for w, ts, te in gs:
                if len(w) < 3:
                    continue
                a = max(0, int(round(ts * fs)))
                b = min(len(x), int(round(te * fs)))
                if (b - a) / fs < min_dur or b - a < 8:
                    continue
                clips.append((np.ascontiguousarray(x[a:b]), fs, w))
        if clips:
            voice_audio[s] = clips
        print(f"  [{s}] {len(clips)} gold-word clips "
              f"({time.time()-t0:.0f}s)", flush=True)
    return voice_audio


def restrict_to_shared_vocab(voice_audio, min_exemplars, max_vocab,
                             min_speakers=2, cap_per_word_per_spk=8):
    """Keep only words that (a) appear in >= min_speakers speakers (so cross-speaker
    recognition is even POSSIBLE) and (b) have >= min_exemplars total exemplars. Cap
    per-word-per-speaker so a frequent function word ('the') does not swamp the set.
    Returns the filtered voice_audio + the kept vocabulary."""
    word_spk = defaultdict(set)
    word_count = defaultdict(int)
    for s, clips in voice_audio.items():
        for _, _, w in clips:
            word_spk[w].add(s)
            word_count[w] += 1
    vocab = {w for w in word_count
             if len(word_spk[w]) >= min_speakers and word_count[w] >= min_exemplars}
    # rank by speaker-spread then count; cap the vocabulary size for tractability.
    ranked = sorted(vocab, key=lambda w: (-len(word_spk[w]), -word_count[w]))
    vocab = set(ranked[:max_vocab])
    out = {}
    for s, clips in voice_audio.items():
        kept = []
        per_word = defaultdict(int)
        for x, fs, w in clips:
            if w in vocab and per_word[w] < cap_per_word_per_spk:
                kept.append((x, fs, w))
                per_word[w] += 1
        if kept:
            out[s] = kept
    return out, vocab


# ---------------------------------------------------------------------------
# Cross-speaker same-word CONSISTENCY (the iter-15 DTW NN over the gammatone band
# trajectory) — a representation-level companion to the graph recognition number.
# Uses the agent's middle-setting cochleagram as the chunk representation.
# ---------------------------------------------------------------------------

def cross_speaker_consistency(voice_audio, max_q=200, seed=0):
    """Same-word CROSS-speaker NN accuracy over the middle-setting cochleagram band
    trajectory. neighbour pool = clips from a DIFFERENT speaker. Returns (acc, n)."""
    from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS
    mid = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
    _, env, dur, nf = mid
    chunks = []   # (band_matrix, word, speaker)
    for s, clips in voice_audio.items():
        for x, fs, w in clips:
            M = cochleagram(x, fs, env, dur, nf)
            if M.shape[0] >= 2:
                chunks.append((np.asarray(M, dtype=np.float64), w, s))
    rng = random.Random(seed)
    by_w = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        by_w[w].append(i)
    q = [i for i, (_, w, s) in enumerate(chunks)
         if any(chunks[j][2] != s for j in by_w[w] if j != i)]
    rng.shuffle(q)
    q = q[:max_q]
    n = len(chunks)
    hit = tot = 0
    for i in q:
        s = chunks[i][2]
        best = (1e18, None)
        for j in range(n):
            if j == i or chunks[j][2] == s:
                continue
            d = full_dtw(chunks[i][0], chunks[j][0])
            if d < best[0]:
                best = (d, j)
        if best[1] is not None:
            tot += 1
            hit += (chunks[best[1]][1] == chunks[i][1])
    return (hit / tot if tot else 0.0), tot


def shuffle_consistency(voice_audio, max_q=200, seed=0):
    """Same metric with word labels permuted (collapse control)."""
    shuffled = {}
    rng = random.Random(seed + 5)
    allw = [w for clips in voice_audio.values() for (_, _, w) in clips]
    perm = list(allw)
    rng.shuffle(perm)
    k = 0
    for s, clips in voice_audio.items():
        out = []
        for x, fs, _ in clips:
            out.append((x, fs, perm[k])); k += 1
        shuffled[s] = out
    return cross_speaker_consistency(shuffled, max_q=max_q, seed=seed)


# ---------------------------------------------------------------------------
# Run the iter-34/35 graph over the continuous gold-span words via build_fold /
# score_fold (the EXACT enriched-graph machinery), LOSO over speakers.
# ---------------------------------------------------------------------------

# Within-manner confusion groups (the landmark's specific target): voiced stops,
# voiceless stops, voiceless fricatives. A confusion is "within-manner" iff the truth
# and the bottom-up's wrong guess share an initial phoneme-class member.
WITHIN_MANNER_GROUPS = {
    "voiced_stop":      set("bdg"),
    "voiceless_stop":   set("ptk"),
    "voiceless_fric":   set("sf"),
}


def _manner_of(word):
    """The within-manner group of a word's INITIAL consonant, or None."""
    if not word:
        return None
    c = word[0].lower()
    for g, members in WITHIN_MANNER_GROUPS.items():
        if c in members:
            return g
    return None


def audit_combine_all_term(n_channels):
    """Audit the variadic product term: it MUST be Argmax(NodesWhere) of
    Times[Attr...], EXACTLY n_channels factors, with NO Max/Sort/Pick/If/Div/weight
    anywhere. Returns (ok, msg). The landmark node enters as one more Attr factor."""
    import domains.many_settings_recognizer as MS
    term = MS.predict_many_settings_term(n_channels)

    def walk(d, types):
        if isinstance(d, dict):
            for k, v in d.items():
                types.add(k) if k == "type" and isinstance(v, str) else None
                if k == "type":
                    types.add(v)
                walk(v, types)
        elif isinstance(d, (list, tuple)):
            for v in d:
                walk(v, types)
    types = set()
    walk(term, types)
    forbidden = {"Max", "Sort", "Pick", "If", "Div", "Weight", "Mul"}
    bad = types & forbidden
    # count the Times factors at the score level
    score = MS.many_settings_score_term(n_channels)

    def count_times_items(d):
        if isinstance(d, dict) and d.get("type") == "Times":
            return len(d.get("items", []))
        return None
    n_factors = count_times_items(score)
    ok = (not bad) and ("Argmax" in types) and ("Times" in types) \
        and (n_factors == n_channels)
    msg = (f"types={sorted(types)}  n_Times_factors={n_factors} "
           f"(expected {n_channels})  forbidden_present={sorted(bad) or 'none'}  "
           f"=> {'PASS' if ok else 'FAIL'}")
    return ok, msg


def error_overlap(fold):
    """The DECISIVE test of the user's mechanism, free of product saturation: on the
    HELD queries where the BOTTOM-UP (the gammatone-only product, iter33) is WRONG,
    what fraction does each orthogonal / AxS cue ALONE get RIGHT? A cue that catches
    the bottom-up's errors is INFORMATIONALLY COMPLEMENTARY even if the saturating
    20-channel product masks it. Returns {cue: (n_bottomup_errors, n_caught)}."""
    tw, hw = fold["train_words"], fold["held_words"]
    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    cands = sorted(set(tw))
    # bottom-up = the gammatone-only product (iter33), per-query predictions.
    bu_pred = EH.heldout_combined(many_tr, many_he, tw, hw, return_preds=True)
    err_idx = [i for i, (p, w) in enumerate(zip(bu_pred, hw)) if p != w]
    # WITHIN-MANNER errors: bottom-up wrong AND the truth & wrong-guess are in the SAME
    # manner group (b/d/g, p/t/k, s/f) — the landmark's specific target population.
    wm_err_idx = [i for i in err_idx
                  if _manner_of(hw[i]) is not None
                  and _manner_of(hw[i]) == _manner_of(bu_pred[i])]
    out = {}
    within_manner = {}     # cue -> (n_within_manner_errors, n_caught_within_manner)
    # each orthogonal cue ALONE (1-NN), per-query prediction on the SAME held set.
    from scripts.many_settings_hvpt_accept import l2  # noqa: F401
    for ci, name in enumerate(fold["ortho_names"]):
        Xtr = np.asarray(ot_tr[ci]); Xtr = Xtr / (np.linalg.norm(Xtr, axis=1, keepdims=True) + 1e-9)
        Xte = np.asarray(ot_he[ci]); Xte = Xte / (np.linalg.norm(Xte, axis=1, keepdims=True) + 1e-9)
        pr = np.asarray(tw)[(Xte @ Xtr.T).argmax(1)]
        caught = sum(int(pr[i] == hw[i]) for i in err_idx)
        out[name] = (len(err_idx), caught)
        wm_caught = sum(int(pr[i] == hw[i]) for i in wm_err_idx)
        within_manner[name] = (len(wm_err_idx), wm_caught)
    # AxS alone (its standalone argmax prediction is precomputed in the fold).
    axs_pred = fold.get("axs_alone_pred", [])
    if axs_pred:
        caught = sum(int(axs_pred[i] == hw[i]) for i in err_idx)
        out["AxS"] = (len(err_idx), caught)
        wm_caught = sum(int(axs_pred[i] == hw[i]) for i in wm_err_idx)
        within_manner["AxS"] = (len(wm_err_idx), wm_caught)
    fold["_within_manner_overlap"] = within_manner
    return out


def run_graph(voice_audio, rounds=2, include_axs=True):
    speakers = sorted(voice_audio)
    real, shuf = [], []
    overlaps = []
    wm_overlaps = []
    for held in speakers:
        if len(voice_audio.get(held, [])) < 2:
            continue
        fold = EH.build_fold(voice_audio, held, rounds, shuffle=False)
        r = EH.score_fold(fold)
        r["error_overlap"] = error_overlap(fold)
        r["within_manner_overlap"] = fold.get("_within_manner_overlap", {})
        _report(r, include_axs)
        real.append(r)
        sr = EH.score_fold(EH.build_fold(voice_audio, held, rounds, shuffle=True))
        _report(sr, include_axs)
        shuf.append(sr)
        overlaps.append(r["error_overlap"])
        wm_overlaps.append(r["within_manner_overlap"])
    return real, shuf, overlaps, wm_overlaps


def _report(r, include_axs):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    key = "enriched" if include_axs else "iter34"
    print(f"\n--- held-out {r['held_voice']}{tag} (held {r['n_held']} "
          f"train {r['n_train']}) ---", flush=True)
    print(f"  GRAPH+landmark {r[key]:.3f}   iter37(F0+modspec) {r.get('iter37', float('nan')):.3f}   "
          f"iter36(3-ortho+AxS) {r.get('iter36', float('nan')):.3f}   "
          f"iter34(noAxS) {r['iter34']:.3f}   iter33(gammatone) {r['iter33']:.3f}   "
          f"single-flat {r['single_flat']:.3f}", flush=True)
    print(f"     AxS: alone {r['axs_alone']:.3f}  label-shuf {r['axs_label_shuf']:.3f}  "
          f"drop-it Δ {r['axs_drop']:+.3f}", flush=True)
    print("     per-ortho: " + "  ".join(
        f"{n}[alone {r['ortho_alone'][n]:.3f}, drop {r['enriched']-r['leave_one_out'][n]:+.3f}]"
        for n in r["ortho_names"]), flush=True)
    if not r["shuffle"] and r.get("error_overlap"):
        eo = r["error_overlap"]
        print("     ERROR-OVERLAP (bottom-up wrong -> cue-alone right): " + "  ".join(
            f"{c}[{caught}/{nerr}]" for c, (nerr, caught) in eo.items()), flush=True)
        wm = r.get("within_manner_overlap", {})
        if wm:
            print("     WITHIN-MANNER (b/d/g,p/t/k,s/f confusion -> cue-alone right): "
                  + "  ".join(f"{c}[{caught}/{nerr}]"
                              for c, (nerr, caught) in wm.items()), flush=True)


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    max_vocab = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    rounds = int(os.environ.get("ROUNDS", "2"))
    include_axs = os.environ.get("AXS", "1") == "1"
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-38 — the LANDMARK node (transient phonetic-event axis) on CONTINUOUS "
          "gold-span words", flush=True)
    print(f"  n_spk={n_spk} utts/spk={utts} min_exemplars={min_ex} "
          f"max_vocab={max_vocab} rounds={rounds} AxS={'on' if include_axs else 'off'}",
          flush=True)
    print(f"  ortho cues = {EH.ORTHO_NAMES}", flush=True)
    print("=" * 72, flush=True)

    # AUDIT the combine-all product (no select, no weight, exactly n factors). The
    # channel count = 20 gammatone + 6 ortho + 1 AxS = 27 (the full graph).
    n_audit = 20 + len(EH.ORTHO_NAMES) + (1 if include_axs else 0)
    ok, msg = audit_combine_all_term(n_audit)
    print(f"\nCOMBINE-ALL AUDIT (n={n_audit}): {msg}", flush=True)
    if not ok:
        print("  AUDIT FAILED — aborting.", flush=True)
        return

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + gold-word slicing...", flush=True)
    va_raw = gather_gold_words(n_spk, utts, wmodel)
    va, vocab = restrict_to_shared_vocab(va_raw, min_ex, max_vocab)
    n_clips = sum(len(c) for c in va.values())
    chance = 1.0 / max(len(vocab), 1)
    print(f"\nshared cross-speaker vocab ({len(vocab)} words, chance {chance:.3f}): "
          f"{sorted(vocab)}", flush=True)
    print(f"speakers kept: {sorted(va)}  total clips: {n_clips}", flush=True)
    # per-word per-speaker coverage
    cov = defaultdict(lambda: defaultdict(int))
    for s, clips in va.items():
        for _, _, w in clips:
            cov[w][s] += 1
    print("word coverage (word: #speakers, #clips):", flush=True)
    for w in sorted(vocab):
        print(f"    {w:14s} {len(cov[w])} spk  {sum(cov[w].values())} clips", flush=True)

    if len(va) < 3 or len(vocab) < 2:
        print("Too few speakers/vocab — aborting.", flush=True)
        return

    # ---- representation-level cross-speaker CONSISTENCY (with shuffle) ----
    print("\n" + "=" * 60, flush=True)
    print("(consistency) cross-speaker same-word DTW-NN (middle cochleagram)",
          flush=True)
    print("=" * 60, flush=True)
    cacc, cn = cross_speaker_consistency(va)
    sacc, sn = shuffle_consistency(va)
    print(f"  cross-speaker NN  {cacc:.3f}  (n={cn})  chance {chance:.3f}", flush=True)
    print(f"  shuffle control   {sacc:.3f}  (n={sn})  => margin {cacc-sacc:+.3f}",
          flush=True)

    # ---- the GRAPH (LOSO over speakers) ----
    print("\n" + "=" * 60, flush=True)
    print("(graph) the enriched recognition graph, LOSO over speakers", flush=True)
    print("=" * 60, flush=True)
    real, shuf, overlaps, wm_overlaps = run_graph(
        va, rounds=rounds, include_axs=include_axs)
    if not real:
        print("No scorable folds — aborting.", flush=True)
        return

    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    gkey = "enriched" if include_axs else "iter34"
    em = mean(real, gkey)
    i37 = mean(real, "iter37")
    i36 = mean(real, "iter36")
    i34 = mean(real, "iter34"); i33 = mean(real, "iter33")
    sf = mean(real, "single_flat"); fr = mean(real, "frozen")
    sem = mean(shuf, gkey); ssf = mean(shuf, "single_flat")
    si36 = mean(shuf, "iter36"); si37 = mean(shuf, "iter37")

    print("\n" + "=" * 72, flush=True)
    print("PART A VERDICT (mean over held-out speakers)", flush=True)
    print("=" * 72, flush=True)
    print(f"  vocab {len(vocab)} words, chance {chance:.3f}", flush=True)
    print(f"  GRAPH+landmark (all cues+AxS)    {em:.3f}", flush=True)
    print(f"  iter37 (F0+modspec, no landmark) {i37:.3f}", flush=True)
    print(f"  iter36 (3-ortho+AxS, no new)     {i36:.3f}", flush=True)
    print(f"  iter34 (no AxS)                  {i34:.3f}", flush=True)
    print(f"  iter33 (gammatone only)          {i33:.3f}", flush=True)
    print(f"  single-setting flat              {sf:.3f}", flush=True)
    print(f"  frozen                           {fr:.3f}", flush=True)
    print(f"  *** GRAPH+landmark vs iter37  Δ {em-i37:+.3f}  "
          f"=> {'WIDENS' if em > i37 else 'does NOT widen'} (the DECISIVE landmark "
          f"delta — does the SHARP transient axis convert where diffuse F0 didn't?)",
          flush=True)
    print(f"  *** GRAPH+landmark vs iter36  Δ {em-i36:+.3f}  "
          f"(the whole source+rate+transient stack vs the filter-only graph)",
          flush=True)
    print(f"  *** GRAPH+landmark vs single-flat Δ {em-sf:+.3f}  (iter36 was {i36-sf:+.3f})",
          flush=True)
    print(f"  SHUFFLE: GRAPH+landmark real {em:.3f} shuffle {sem:.3f} => margin {em-sem:+.3f} "
          f"({'CLEAN' if em > sem else 'NOT CLEAN'})", flush=True)
    print(f"           iter37 real {i37:.3f} shuffle {si37:.3f} => margin {i37-si37:+.3f}",
          flush=True)
    print(f"           iter36 real {i36:.3f} shuffle {si36:.3f} => margin {i36-si36:+.3f}",
          flush=True)
    print(f"           single-flat real {sf:.3f} shuffle {ssf:.3f} => margin {sf-ssf:+.3f}",
          flush=True)

    print("\n  PER-NODE DROP-IT (mean over folds) — which DIGIT-REDUNDANT cues are "
          "CONTINUOUS-COMPLEMENTARY?", flush=True)
    axs_alone = mean(real, "axs_alone"); axs_drop = mean(real, "axs_drop")
    axs_label = mean(real, "axs_label_shuf")
    print(f"    AxS               alone {axs_alone:.3f}  label-shuf {axs_label:.3f}  "
          f"drop-it Δ {axs_drop:+.3f}  "
          f"=> {'COMPLEMENTARY' if axs_drop > 0 else 'redundant/neutral'}", flush=True)
    for n in EH.ORTHO_NAMES:
        alone = float(np.mean([r["ortho_alone"][n] for r in real]))
        drop = float(np.mean([r["enriched"] - r["leave_one_out"][n] for r in real]))
        print(f"    {n:18s} alone {alone:.3f}  drop-it Δ {drop:+.3f}  "
              f"=> {'COMPLEMENTARY' if drop > 0 else 'redundant/hurts'}", flush=True)

    print("\n  ERROR-OVERLAP (decisive, free of product saturation) — on the held "
          "queries where the BOTTOM-UP (gammatone product) is WRONG, what fraction "
          "does each cue ALONE catch?", flush=True)
    agg = defaultdict(lambda: [0, 0])
    for eo in overlaps:
        for c, (nerr, caught) in eo.items():
            agg[c][0] += nerr
            agg[c][1] += caught
    for c in sorted(agg):
        nerr, caught = agg[c]
        rate = caught / max(nerr, 1)
        print(f"    {c:18s} catches {caught}/{nerr} of bottom-up errors = {rate:.3f}  "
              f"(chance {chance:.3f}; >chance => COMPLEMENTARY information the "
              f"bottom-up lacks)", flush=True)

    print("\n  WITHIN-MANNER CONFUSION ANALYSIS (the landmark's SPECIFIC target) — on "
          "the held queries where the bottom-up confuses WITHIN a manner class "
          "(b/d/g, p/t/k, s/f), what fraction does each cue ALONE catch?", flush=True)
    wm_agg = defaultdict(lambda: [0, 0])
    for wm in wm_overlaps:
        for c, (nerr, caught) in wm.items():
            wm_agg[c][0] += nerr
            wm_agg[c][1] += caught
    total_wm = max((v[0] for v in wm_agg.values()), default=0)
    if total_wm == 0:
        print("    (no within-manner confusions occurred in this vocab/fold set — the "
              "function-word vocab has few b/d/g,p/t/k,s/f minimal pairs; the landmark's "
              "target population is ABSENT here, so it can only sit near-flat)",
              flush=True)
    else:
        for c in sorted(wm_agg):
            nerr, caught = wm_agg[c]
            rate = caught / max(nerr, 1)
            print(f"    {c:18s} catches {caught}/{nerr} within-manner confusions = "
                  f"{rate:.3f}  (chance {chance:.3f}; landmark > chance AND > the filter "
                  f"cues => it resolves the transient confusions)", flush=True)

    print("\nHONEST: gold word spans (faster-whisper forced alignment) ISOLATE the "
          "recognition graph from the segmentation problem — the bottom-up still fails "
          "on coarticulation + cross-speaker, which is exactly where the orthogonal / "
          "top-down cues should become complementary. Combine-all, no fit, no select, "
          "no weight; the graph is the iter-34/35 product UNCHANGED.", flush=True)


if __name__ == "__main__":
    main()

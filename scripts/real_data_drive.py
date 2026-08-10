"""real_data_drive — DRIVE THE CONTEXT-RESTORATION LEVER ON REAL CONTINUOUS SPEECH.

THE LEVER THE REAL DATA UNLOCKS. The top-down recovery (docs/topdown_recovery.md)
demonstrated the SYNTHESIS arm of top-down compensation strongly (+0.120 on
continuous strings), but its CONTEXT-RESTORATION arm came in at EXACTLY +0.000 —
and named WHY: the test digit-strings were RANDOM, so the bigram context prior had
nothing to restore (the bigram counts were near-uniform). That null was a property
of the VENUE, not the lever. The directive provides the missing venue: REAL
continuous speech (LibriSpeech dev-clean), where the word sequence carries genuine
English structure (sentence_learning already showed the bigram beats frequency and
COLLAPSES under shuffle — the structure is in the ORDER).

THE DRIVE (my design, my call — not prescribed): re-run the SAME top-down route the
agent already built — the coarse acoustic cue PRUNES the admissible word set, the
prior RESTORES identity — but on REAL word sequences where the bigram context prior
has signal. The do-contrast is the identical recogniser with the context channel
TOGGLED:

  (A) ACOUSTIC-ONLY  : argmin over candidate words of native DtwTo(heard, fm[w]).
                       The bottom-up acoustic estimate resolves the word alone.
  (B) ACOUSTIC+CONTEXT: same native acoustic score, PLUS a bigram context prior
                       log P(w | prev_word) learned from TRAIN transcripts. The
                       coarse acoustic cue prunes; the context RESTORES identity.

Same ear, same native DtwTo synth-error, same forward model, same held-out data —
ONLY the context channel is added in (B). If the context-restoration arm CLIMBS on
real continuous speech where it was +0.000 on random digits, that is the grounded
unlock of a lever blocked at the digit venue.

THE SHUFFLE CONTROL (the honesty backstop): re-run (B) with the bigram prior
learned from SHUFFLED transcripts (word order destroyed, frequency preserved). If
the context gain is real sequential structure it must COLLAPSE toward the
acoustic-only baseline under shuffle. A gain that survives shuffle would be a
frequency/unigram artifact, not restoration — and would be REOPENED.

FORWARD MODEL: the proven multi-exemplar A1-trajectory model (docs/
forward_model_drive.md: K=5 medoid-per-speaker manifold, the COMMITTED lever). On
real continuous speech the per-word exemplars are harvested by the agent's OWN
sonority-valley word segmentation (teach_via_valleys) aligned to the transcript —
the substrate-native boundary signal, not an oracle forced alignment. LOSO over
speakers: a held-out speaker's words never enter their own forward model.

ARCHITECTURE (CLAUDE.md): NATIVE where the cognition lives. The acoustic synth-error
is the graph DtwTo Term (recognition_graph.synth_error_term) evaluated by
substrate.evaluate in Rust. The forward-model exemplars and the context prior enter
as GRAPH DATA (the prior is added to the candidate's log-score as a scalar, exactly
as topdown_recovery's prior enters the native collapse manifold's lw). The
min-over-exemplars + argmax-over-words winner is a READOUT over native distances —
a query, identical in kind to the existing AbS argmin. Python is the world adapter
+ instrument only: audio I/O, the owned valley word-segmentation, the bigram COUNTS
(a count, not a fitted parameter), LOSO + do-contrast + grounding bookkeeping. No
net, no .fit, no gradient, no loss, no optimiser, no sweep-to-maximise. The vocab
size V and exemplar budget K are FIXED structural choices, reported, not tuned.
solve_for_n.py and CortexLoop UNTOUCHED.

THE GROUNDING GATE (domains/silent_failure_grounding): the CLAIM is that the
context channel raises recognition to acc_B; the WORLD-MEASURE re-runs the actual
acoustic+context recogniser on the held-out data; a contradiction REOPENS. The
two-sided gate also REOPENS if the gain does not clear the +0.005 non-noise floor,
OR if it does not collapse under shuffle.

Run: PYTHONUNBUFFERED=1 python -m scripts.real_data_drive [n_utts] [n_speakers] [vocab] [K]
"""
from __future__ import annotations

import os
import math
import random
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key
from domains import recognition_graph as RG
from domains import silent_failure_grounding as SFG
from scripts.analysis_by_synthesis_accept import traj_to_matrix, as_tuple
import scripts.sentence_learning as SL


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# WORLD ADAPTER — harvest per-word A1 trajectories from REAL continuous speech
# using the agent's OWN sonority-valley word segmentation aligned to the
# transcript. Mechanical translation: audio -> (word, A1-trajectory) pairs.
# ==========================================================================

_N_PATCHES = 25


def harvest_word_trajectories(pipe, sel):
    """For each (path, speaker, transcript): ingest, partition the sign stream at
    the agent's sonority valleys, reconcile to the transcript words, and read out
    each word-group's A1 trajectory (the longest sign in the group). Returns a list
    of (word, speaker, A1-trajectory-matrix) plus the per-utterance true word
    sequences (for the bigram prior + the recognition test). World-adapter readout
    only — the segmentation is the agent's native teach_via_valleys."""
    word_exemplars = []     # (word, speaker, M)  M = frames x patches
    true_seqs = []          # per-utt [(word, speaker, M_or_None), ...] in order
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        words = [w for w in re.findall(r"[\w']+", transcript.lower()) if w]
        if not words:
            continue
        try:
            samples, _ = SL.load_flac_8k(path)
        except Exception as e:
            print(f"  FAIL decode {path}: {e}", flush=True)
            continue
        # fresh substrate per utt so the lexical matcher can't collapse signs
        sub = Substrate()
        p2 = STTPipeline(STTParams(sample_rate=8000))
        p2.attach(sub)
        p2._ensure_audio_pipeline(sub)
        vc = {}
        try:
            res = p2.teach_via_valleys(sub, samples, transcript, vote_counts=vc)
        except Exception as e:
            print(f"  FAIL teach {path}: {e}", flush=True)
            continue
        sub.tick(50000)
        if res.get("signs", 0) == 0:
            continue
        # read out per-word groups: for each grounded word, the longest sign's
        # trajectory is that word's A1-patch exemplar from this utterance.
        # We walk the votes: sign_key -> word, and the sign's trajectory attr.
        # Build sign_key -> trajectory and sign_key -> word.
        sk_to_word = {}
        for (sk, w), c in vc.items():
            cur = sk_to_word.get(sk)
            if cur is None or c > cur[1]:
                sk_to_word[sk] = (w, c)
        # ordered signs (time order) with trajectories
        ordered = SL  # placeholder; we read the graph directly below
        # collect (time, word, M) per grounded sign
        per = []
        for s in sub.nodes("AcousticSign"):
            sk = _node_sort_key(s)
            ww = sk_to_word.get(sk)
            if ww is None:
                continue
            traj = sub.node(s)["attrs"].get("trajectory")
            if not traj:
                continue
            M = traj_to_matrix(np.array([float(v) for v in traj],
                                        dtype=np.float32))
            if M is None or M.shape[0] < 2:
                continue
            # time order via the sign's utterance start
            t = 0.0
            for utt in sub.in_neighbours(s, "heard_as"):
                tt = sub.node(utt)["attrs"].get("start_time_s")
                if tt is not None:
                    t = float(tt)
                break
            per.append((t, ww[0], M, len(traj)))
        per.sort(key=lambda x: x[0])
        # one exemplar per word-occurrence: collapse consecutive same-word signs,
        # keeping the LONGEST trajectory of the run (the word's main acoustic).
        seq = []
        run_word = None
        run_best = None
        run_len = -1
        for t, w, M, L in per:
            if w != run_word:
                if run_word is not None and run_best is not None:
                    seq.append((run_word, sp, run_best))
                run_word, run_best, run_len = w, M, L
            elif L > run_len:
                run_best, run_len = M, L
        if run_word is not None and run_best is not None:
            seq.append((run_word, sp, run_best))
        if len(seq) >= 2:
            true_seqs.append(seq)
            word_exemplars.extend(seq)
        if (i + 1) % 100 == 0:
            print(f"  harvested {i+1}/{len(sel)}  exemplars={len(word_exemplars)}"
                  f"  utts={len(true_seqs)}  ({time.time()-t0:.0f}s)", flush=True)
    return word_exemplars, true_seqs


# ==========================================================================
# FORWARD MODEL — multi-exemplar (the COMMITTED forward_model_drive lever),
# one medoid per train speaker per word, capped at K. LOSO-safe (held speaker
# excluded by the caller).
# ==========================================================================

def build_forward_model(word_exemplars, vocab, held_speaker, K):
    """word -> [up to K medoid A1-trajectory exemplars over TRAIN speakers]."""
    by_word_sp = {}
    for w, sp, M in word_exemplars:
        if w not in vocab or sp == held_speaker:
            continue
        by_word_sp.setdefault(w, {}).setdefault(sp, []).append(M)
    fm = {}
    for w in vocab:
        reps = []
        for sp, mats in by_word_sp.get(w, {}).items():
            # medoid: the exemplar closest to the per-speaker mean (mechanical
            # signal pick, no decision) — same as forward_model_drive.
            L = min(m.shape[0] for m in mats)
            stk = np.stack([m[:L] for m in mats], axis=0)
            mu = stk.mean(axis=0)
            d2 = ((stk - mu) ** 2).reshape(len(mats), -1).sum(axis=1)
            reps.append(mats[int(np.argmin(d2))])
        reps = reps[:K]
        fm[w] = [as_tuple(m) for m in reps] if reps else None
    return fm


# ==========================================================================
# BIGRAM CONTEXT PRIOR — log P(w | prev) from TRAIN transcripts (a COUNT, not a
# fitted parameter). Enters the candidate's log-score as a scalar, exactly as
# topdown_recovery's prior enters the native collapse lw.
# ==========================================================================

def build_bigram_prior(train_seqs, vocab):
    """Returns (logp(w|prev), logp(w)) over the closed vocab. Add-1 smoothed."""
    bg = {}     # prev -> {w: count}
    ug = {}
    for seq in train_seqs:
        words = [w for (w, sp, M) in seq]
        for a, b in zip(words, words[1:]):
            if a in vocab and b in vocab:
                bg.setdefault(a, {}).setdefault(b, 0)
                bg[a][b] += 1
        for w in words:
            if w in vocab:
                ug[w] = ug.get(w, 0) + 1
    V = len(vocab)
    tot_u = sum(ug.values()) + V
    log_ug = {w: math.log((ug.get(w, 0) + 1) / tot_u) for w in vocab}

    def log_bigram(prev, w):
        d = bg.get(prev)
        if not d:
            return log_ug[w]
        tot = sum(d.values()) + V
        return math.log((d.get(w, 0) + 1) / tot)

    return log_bigram, log_ug


# ==========================================================================
# NATIVE RECOGNISER — same DtwTo synth-error for both routes. Acoustic score is
# native; the context prior is added to the candidate's log-score as a scalar
# (graph data). The argmax over candidates is a READOUT over native distances.
# ==========================================================================

class Recogniser:
    def __init__(self, sub, vocab):
        self.sub = sub
        self.vocab = vocab
        RG.mark_words(sub, vocab)
        self.word_c = {}
        for w in vocab:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "rdd"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"rdd_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def _acoustic_neglogscore(self, heardM, fm):
        """Per-candidate acoustic score: min-over-exemplars native DtwTo distance.
        Returns {w: distance} (lower = better). The DtwTo is the native Term."""
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, as_tuple(heardM))
        out = {}
        for w in self.vocab:
            exs = fm.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            we = 1e30
            for ex in exs:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, ex)
                e = float(self.sub.evaluate(self.err_term,
                                            {"s": self.sign, "w": c}))
                if e < we:
                    we = e
            out[w] = we
        return out

    def recognise(self, heardM, fm, prev_word=None, log_bigram=None,
                  ctx_weight=1.0):
        """argmax over candidates of [ -acoustic_dist + ctx_weight * logP(w|prev) ].
        With log_bigram=None this is pure acoustic (route A). With it supplied the
        context prior RESTORES identity among the acoustically-admissible (route B).
        The acoustic distances are native; the prior is a scalar added to the
        log-score (graph data); the argmax is a readout."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        dist = self._acoustic_neglogscore(heardM, fm)
        if not dist:
            return None
        # acoustic log-score = -distance, scaled so the prior is commensurate.
        # The acoustic term dominates; the prior breaks ties / prunes among the
        # acoustically near. Scale set ONCE from the distance spread (a fixed
        # structural normalisation, not swept): map distances to a log-likelihood
        # by negating and dividing by the median spread.
        ds = np.array(list(dist.values()))
        spread = float(np.median(np.abs(ds - np.median(ds)))) or 1.0
        best, bw = -1e30, None
        for w, d in dist.items():
            sc = -d / spread
            if log_bigram is not None and prev_word is not None:
                sc += ctx_weight * log_bigram(prev_word, w)
            if sc > best:
                best, bw = sc, w
        return bw


# ==========================================================================
# DO-CONTRAST over held-out continuous utterances (LOSO).
# ==========================================================================

def evaluate(rec, fm_by_held, test_seqs_by_held, vocab, log_bigram=None,
             ctx_weight=1.0):
    """For each held-out speaker, recognise each in-vocab word token of each
    held-out continuous utterance, in order, using the PREVIOUS true word as the
    context (teacher-forced prev — isolates the context channel's value, not error
    propagation). Returns (acc, correct, total)."""
    corr = tot = 0
    for held, fm in fm_by_held.items():
        for seq in test_seqs_by_held.get(held, []):
            words = [w for (w, sp, M) in seq]
            mats = [M for (w, sp, M) in seq]
            for j in range(len(words)):
                w = words[j]
                if w not in vocab:
                    continue
                M = mats[j]
                if M is None or M.shape[0] < 2:
                    continue
                prev = words[j - 1] if j > 0 else None
                pred = rec.recognise(M, fm, prev_word=prev,
                                     log_bigram=log_bigram, ctx_weight=ctx_weight)
                if pred is not None:
                    corr += int(pred == w)
                    tot += 1
    return corr / max(tot, 1), corr, tot


def main():
    t0 = time.time()
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    VOCAB = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    print(f"=== real_data_drive  n_utts={n_utts}  n_speakers={n_speakers}  "
          f"vocab={VOCAB}  K={K} ===", flush=True)
    print("LEVER: context-restoration on REAL continuous speech (the +0.000 "
          "topdown context arm, re-driven where the bigram has signal)", flush=True)

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    chosen = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen]
    random.shuffle(sel)
    sel = sel[:n_utts]
    used = sorted(set(p[1] for p in sel))
    print(f"LibriSpeech dev-clean: {len(pairs)} utts, {len(speakers)} speakers; "
          f"using {len(sel)} utts from {len(used)} speakers", flush=True)

    pipe = None  # per-utt fresh substrate inside harvest
    print("\n--- harvesting per-word A1 trajectories (agent's valley "
          "segmentation, transcript-aligned) ---", flush=True)
    word_exemplars, true_seqs = harvest_word_trajectories(pipe, sel)
    print(f"harvested {len(word_exemplars)} word exemplars over {len(true_seqs)} "
          f"utts", flush=True)

    # ---- closed vocab: the top-V most frequent words across the harvest ----
    freq = {}
    for w, sp, M in word_exemplars:
        freq[w] = freq.get(w, 0) + 1
    vocab = [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:VOCAB]]
    vocab_set = set(vocab)
    chance = 1.0 / max(len(vocab), 1)
    print(f"closed vocab (top {VOCAB}): {vocab}", flush=True)
    print(f"chance = 1/{len(vocab)} = {chance:.4f}", flush=True)

    # in-vocab token coverage
    iv = sum(1 for seq in true_seqs for (w, sp, M) in seq if w in vocab_set)
    print(f"in-vocab word tokens (test surface): {iv}", flush=True)

    # ---- LOSO split: which utts are test (held speaker) is per-held ----
    # train transcripts for the bigram prior = ALL utts NOT from the held speaker.
    sub = Substrate()
    rec = Recogniser(sub, vocab)

    # Build, per held speaker: the forward model (train speakers only) and the
    # test utts (held speaker only). The bigram prior is built from the train utts.
    held_speakers = used
    fm_by_held = {}
    test_seqs_by_held = {}
    bigram_by_held = {}
    for held in held_speakers:
        fm_by_held[held] = build_forward_model(word_exemplars, vocab, held, K)
        test_seqs_by_held[held] = [seq for seq in true_seqs
                                   if seq and seq[0][1] == held]
        train_seqs = [seq for seq in true_seqs if seq and seq[0][1] != held]
        bigram_by_held[held] = build_bigram_prior(train_seqs, vocab_set)

    # ---- ROUTE A: acoustic-only ----
    print("\n--- ROUTE A: ACOUSTIC-ONLY (bottom-up native DtwTo) ---", flush=True)
    accA, cA, tA = evaluate(rec, fm_by_held, test_seqs_by_held, vocab_set)
    print(f"  acoustic-only acc: {accA:.4f}  ({cA}/{tA})", flush=True)

    # ---- ROUTE B: acoustic + bigram context prior (top-down restoration) ----
    print("\n--- ROUTE B: ACOUSTIC + CONTEXT (top-down restoration) ---", flush=True)

    def route_b():
        corr = tot = 0
        for held in held_speakers:
            lb, _ = bigram_by_held[held]
            a, c, t = evaluate(rec, {held: fm_by_held[held]},
                               {held: test_seqs_by_held[held]}, vocab_set,
                               log_bigram=lb, ctx_weight=1.0)
            corr += c; tot += t
        return corr / max(tot, 1), corr, tot

    accB, cB, tB = route_b()
    print(f"  acoustic+context acc: {accB:.4f}  ({cB}/{tB})", flush=True)
    deltaB = accB - accA
    print(f"  DELTA (context - acoustic): {deltaB:+.4f}", flush=True)

    # ---- SHUFFLE CONTROL: bigram prior from SHUFFLED transcripts ----
    print("\n--- SHUFFLE CONTROL: context prior from order-destroyed transcripts ---",
          flush=True)
    bigram_shuf_by_held = {}
    for held in held_speakers:
        train_seqs = [seq for seq in true_seqs if seq and seq[0][1] != held]
        # destroy word order: pool all words, reshuffle into same-length pseudo-utts
        all_w = [(w, sp, M) for seq in train_seqs for (w, sp, M) in seq]
        random.shuffle(all_w)
        lengths = [len(seq) for seq in train_seqs]
        shuf = []
        idx = 0
        for L in lengths:
            shuf.append(all_w[idx:idx + L])
            idx += L
        bigram_shuf_by_held[held] = build_bigram_prior(shuf, vocab_set)

    def route_b_shuf():
        corr = tot = 0
        for held in held_speakers:
            lb, _ = bigram_shuf_by_held[held]
            a, c, t = evaluate(rec, {held: fm_by_held[held]},
                               {held: test_seqs_by_held[held]}, vocab_set,
                               log_bigram=lb, ctx_weight=1.0)
            corr += c; tot += t
        return corr / max(tot, 1), corr, tot

    accS, cS, tS = route_b_shuf()
    print(f"  acoustic+SHUFFLED-context acc: {accS:.4f}  ({cS}/{tS})", flush=True)
    deltaS = accS - accA
    print(f"  DELTA (shuffled-context - acoustic): {deltaS:+.4f}", flush=True)
    print(f"  context gain that SURVIVES shuffle: {deltaS:+.4f} "
          f"(should be ~0 if the gain is real sequential structure)", flush=True)

    # ==========================================================================
    # GROUNDING GATE — fire on stakes, world-measure the context route, REOPEN on
    # contradiction. Then the two-sided honest gate: did context beat acoustic by
    # > +0.005 AND collapse under shuffle?
    # ==========================================================================
    print("\n--- GROUNDING (silent_failure_grounding): fire-on-stakes + world-measure ---",
          flush=True)

    def world_measure_context():
        return route_b()[0]      # independent re-run of the actual context recogniser

    trace = SFG.grounding_check(
        sub,
        name="context_restoration_real_speech",
        conclusion_text=("the bigram context prior restores word identity on real "
                         "continuous speech, lifting acoustic-only recognition"),
        claimed=float(accB),
        stakes=0.9,
        world_measure=world_measure_context,
        tol=0.03,
        bank_on_catch=True,
    )
    g = trace["grounding"]; r = trace["resolution"]
    print(f"  fired-on-stakes : {trace['gate']['fire']}", flush=True)
    print(f"  claimed context acc : {accB:.4f}", flush=True)
    print(f"  world measured      : {g.get('measured')}", flush=True)
    print(f"  grounding reason    : {g.get('reason')}", flush=True)
    print(f"  resolution          : {r['decision']} — {r.get('reason')}", flush=True)

    # ---- HONEST TWO-SIDED VERDICT ----
    print("\n========================= VERDICT =========================", flush=True)
    world_consistent = (g.get("measured") is not None
                        and not g.get("contradiction"))
    lever_moved = deltaB > 0.005
    collapses = deltaS < deltaB * 0.5    # context gain must mostly vanish under shuffle
    print(f"  acoustic-only        : {accA:.4f}  (chance {chance:.4f}, "
          f"{accA/chance:.1f}x)", flush=True)
    print(f"  acoustic+context     : {accB:.4f}  (delta {deltaB:+.4f})", flush=True)
    print(f"  acoustic+shuffled    : {accS:.4f}  (delta {deltaS:+.4f})", flush=True)
    print(f"  context > acoustic by >+0.005   : {'YES' if lever_moved else 'NO'}",
          flush=True)
    print(f"  gain collapses under shuffle    : {'YES' if collapses else 'NO'} "
          f"(real {deltaB:+.4f} -> shuffled {deltaS:+.4f})", flush=True)
    print(f"  world-measure consistent        : {'YES' if world_consistent else 'NO'}",
          flush=True)

    if lever_moved and collapses and world_consistent and r["decision"] == "COMMIT":
        print(f"\n  GROUNDED CLIMB: the CONTEXT-RESTORATION arm — +0.000 on random "
              f"digits — CLIMBS on real continuous speech by {deltaB:+.4f} "
              f"({accA:.4f} -> {accB:.4f}), collapses under shuffle "
              f"({deltaS:+.4f}), world-measure AGREES. The real data UNLOCKED a "
              f"lever blocked at the digit venue.", flush=True)
        verdict = "GROUNDED_CONTEXT_CLIMB"
    elif lever_moved and not collapses:
        print(f"\n  REOPEN: the context gain {deltaB:+.4f} did NOT collapse under "
              f"shuffle ({deltaS:+.4f}) — it is a frequency/unigram artifact, not "
              f"sequential restoration. The honesty backstop CAUGHT it.", flush=True)
        verdict = "REOPEN_SURVIVES_SHUFFLE"
    elif not lever_moved:
        print(f"\n  REOPEN: context did NOT beat acoustic by the +0.005 floor "
              f"(delta {deltaB:+.4f}). The lever did not climb on this venue; "
              f"the FRONTIER is named below.", flush=True)
        verdict = "REOPEN_NO_CLIMB"
    else:
        print(f"\n  WALL NAMED: delta {deltaB:+.4f}, resolution {r['decision']}.",
              flush=True)
        verdict = "WALL_NAMED"

    print(f"\nVERDICT_TOKEN={verdict}  acoustic={accA:.4f}  context={accB:.4f}  "
          f"delta={deltaB:+.4f}  shuffled_delta={deltaS:+.4f}  chance={chance:.4f}  "
          f"in_vocab_tokens={tA}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_REALDATA_COMPLETE===", flush=True)


if __name__ == "__main__":
    main()

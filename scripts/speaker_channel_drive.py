"""speaker_channel_drive — A DEDICATED, SEPARABLE SPEAKER CHANNEL.

THE STRUCTURE three independent lines converged on this session:
  · DISSOCIATION (ozma_speech_disorders_dissociate_components): PHONAGNOSIA =
    voice/speaker recognition BROKEN with word comprehension PRESERVED. The two
    dissociate -> speaker identity is a SEPARABLE structure from word content.
    Recognition should NOT be one entangled pipeline; it should be the distinct
    admissible structures the disorder tails pull apart.
  · The agent's OWN #1 gap (gap_prioritiser): cross-speaker invariance (payoff 82).
  · The live cross-speaker ceiling: real human held-out speaker ~0.15-0.42 while
    same-speaker is easy — the cross-speaker wall, surfaced autonomously.

THE ARCHITECTURE (motivated by the dissociation; the AGENT's owned pieces, composed
— NOT a normalization tweak). Split the heard signal into TWO SEPARABLE structures:

  (1) the SPEAKER CHANNEL — estimate the speaker's identity as its OWN first-class
      structure: a Speaker node carrying the talker's VTL proxy (the energy-weighted
      mean log-spectral centre-of-mass, the formant centre-of-mass = the agent's owned
      VTL estimate, traj_log_centroid / estimate_vtl_logalpha). This is exactly what
      phonagnosia recognises: WHO is speaking (their tract length / voice), estimated
      LABEL-FREE from the token itself. It is a node in the graph, not a warp buried
      in the front-end.

  (2) the speaker-INVARIANT CONTENT CHANNEL — FACTOR the speaker estimate OUT: warp
      the heard trajectory's log-frequency axis so the talker's own centroid lands on
      a fixed canonical tract (owned warp_bands), removing the speaker term and leaving
      the speaker-invariant CONTENT. Recognition runs on the CONTENT channel.

The KEY that makes this the SEPARABLE-CHANNEL architecture (not the known cohort-VTL
null, commit 9ae4fd68): BOTH sides are factored to their OWN per-token speaker
estimate. Each heard token estimates ITS speaker and removes IT; each manifold
exemplar was ALSO factored to ITS speaker when the manifold was built. So the DtwTo
compares CONTENT-vs-CONTENT — two utterances each stripped of their own speaker — not
"everyone warped to one blurred cohort mean" (the null warps every token to a single
speaker-blind cohort centroid; this estimates and removes EACH token's OWN speaker as
a separate structure). That is the dissociation made structural: the speaker channel
is estimated and removed per token as its own object, exactly as phonagnosia isolates
it.

THE DO-CONTRAST (one ear, one native recogniser, two ARCHITECTURES, same data, LOSO
held-out speaker):
  (A) ENTANGLED — recognise directly on the raw trajectory, NO separate speaker
      channel (the current one-pipeline form). Native DtwTo argmin over the word
      exemplar manifold.
  (B) SEPARABLE — estimate the speaker channel (per token), factor it out -> content
      channel -> the SAME native DtwTo argmin over the manifold (whose exemplars were
      ALSO factored to their own speaker). Two separable structures, not one pipeline.
  Same heard trajectory, same native DtwTo Term, same exemplar manifold, same argmin
  readout. The ONLY thing that changes is the separate speaker channel.
  Plus a SHUFFLE control: permute the exemplar labels; if (B)'s gain survives the
  shuffle it is an artifact, not structure.

ARCHITECTURE (CLAUDE.md): NATIVE where the cognition lives. The recognition DECISION
is the graph DtwTo Term (recognition_graph.synth_error_term) evaluated by
substrate.evaluate in Rust in BOTH arms — NO numpy computes a recognition score. The
speaker estimate is the agent's OWNED inverse (estimate_vtl_logalpha / traj_log_centroid
= read the formant centre-of-mass; warp_bands = the log-freq shift) — NOT a fitted
optimiser, NO gradient, NO sweep, NO loss. The argmin-over-words + min-over-exemplars
is a READOUT over native distances (a query, identical in kind to the existing AbS
winner readout). Python is WORLD ADAPTER + instrument ONLY: audio I/O, A1 trajectory
extraction, LOSO bookkeeping, the do-contrast + grounding measurement. K (exemplar
budget) is a FIXED structural choice reported across, never swept-to-max.
solve_for_n.py / weighted_admissibility.py / CortexLoop UNTOUCHED.

GROUNDING (honest, critical): prior speaker work was MODEST/NULL — speaker_norm +3%,
cohort-VTL warp an honest NULL on 6-speaker FSDD. A normalization PATCH is known-weak.
The novelty here is the EXPLICIT SEPARATE CHANNEL (estimate speaker as its own
structure + factor it out + recognise on the invariant content), motivated by the
dissociation. If it STILL nulls, that is REPORTED PLAINLY as the result (the separable
channel does not beat the entangled pipeline on this venue) with the reason (speaker
estimate too blurry / venue wrong) — NO manufactured gain, NO sweep.

VENUE: real human cross-speaker. Default = Google Speech Commands held-out-speaker
(/tmp/sc, ~2000 speakers — where invariance is the ACTUAL limit, agent diagnosed it at
42%/15%). FSDD held-out-speaker (6 speakers) is the secondary venue (the task flags it
may be exhausted: cohort-VTL nulled there).

Run: PYTHONUNBUFFERED=1 python -m scripts.speaker_channel_drive \
        [venue=sc|fsdd] [n_words] [n_per_word_train] [n_test] [K]
"""
from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import recognition_graph as RG
from domains.invariant_units import (
    band_centres, estimate_vtl_logalpha, warp_bands, cmvn,
    _spectral_centroid_log,
)
from scripts.invariant_units_accept import band_trajectory_matrix
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple,
)
from scripts.fsdd_learner_world import load_wav, gather_files
import scripts.real_speech as RSP

random.seed(1)

# A fixed canonical tract the speaker channel factors EVERY token onto. Chosen as the
# midpoint of the agent's log-frequency band axis (a fixed structural reference, NOT
# the cohort mean — the point is to remove EACH token's OWN speaker, not warp to the
# pool average). Reported, never swept.
_CANONICAL_LOG = float(np.log(band_centres(32)).mean())


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# THE SPEAKER CHANNEL — estimate the speaker's identity as its OWN structure.
# The talker's VTL proxy = the energy-weighted mean log-spectral centre-of-mass
# (the formant centre-of-mass the agent's estimate_vtl_logalpha reads off). This
# is WHO is speaking — what phonagnosia recognises — estimated LABEL-FREE from the
# token. We materialise it as a first-class Speaker node carrying that parameter.
# ==========================================================================

def estimate_speaker(M_raw: np.ndarray, voiced_floor: float = 0.25) -> float:
    """The SPEAKER CHANNEL: estimate the talker's VTL identity (log-spectral
    centre-of-mass over voiced frames) from the token ITSELF, no label. This is the
    separable structure phonagnosia isolates: the voice/tract, independent of the word.
    """
    M = np.asarray(M_raw, dtype=np.float64)
    log_lc = np.log(band_centres(M.shape[1]))
    fe = M.sum(axis=1)
    if fe.max() <= 1e-12:
        return float(log_lc.mean())
    voiced = fe >= voiced_floor * fe.max()
    if voiced.sum() == 0:
        voiced = np.ones(M.shape[0], dtype=bool)
    cents = [_spectral_centroid_log(M[f], log_lc) for f in np.where(voiced)[0]]
    return float(np.mean(cents))


def factor_out_speaker(M_raw: np.ndarray, speaker_log_centroid: float) -> np.ndarray:
    """The CONTENT CHANNEL: FACTOR the estimated speaker OUT. Warp the token's
    log-frequency axis so ITS OWN speaker centroid lands on the fixed canonical tract
    (owned warp_bands), removing the speaker term, then CMVN. What's left is the
    speaker-invariant CONTENT. log alpha = (this token's speaker centroid) - canonical;
    warp_bands shifts the spectrum by -log alpha onto the canonical tract."""
    log_alpha = speaker_log_centroid - _CANONICAL_LOG
    return cmvn(warp_bands(np.asarray(M_raw, dtype=np.float64), log_alpha),
                do_variance=True)


def materialise_speaker_node(sub, M_raw):
    """Lay the SPEAKER CHANNEL out as a first-class graph node (the separable
    structure, not a buried warp): a Speaker node carrying the estimated VTL proxy.
    Mechanical I/O translation (estimate -> node attr); the estimate is the agent's
    owned quantity. Returns (speaker_node, speaker_log_centroid)."""
    slc = estimate_speaker(M_raw)
    node = sub.add_node("Speaker", {"vtl_log_centroid": float(slc),
                                    "channel": "speaker_identity"})
    return node, slc


# ==========================================================================
# THE NATIVE RECOGNISER — the SAME graph DtwTo synth-error for BOTH arms. The
# per-exemplar DtwTo is native (substrate.evaluate); min-over-exemplars +
# argmin-over-words is a READOUT over the native distances (a query).
# ==========================================================================

class Recogniser:
    def __init__(self, sub, words):
        self.sub = sub
        self.words = list(words)
        RG.mark_words(sub, self.words)
        self.word_c = {}
        for w in self.words:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "spkchan"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"spkchan_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def match(self, heard_tuple, manifold):
        """argmin over words of [ min over exemplars of native DtwTo(heard, ex) ].
        `heard_tuple` is the as_tuple(frames x bands) form (a graph attr). The DtwTo
        is evaluated natively in Rust; the min + argmin are READOUTS over the native
        distances. Returns the predicted word (or None)."""
        if heard_tuple is None or len(heard_tuple) < 2:
            return None
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, heard_tuple)
        best, bw = 1e30, None
        for w in self.words:
            exs = manifold.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            for ex in exs:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, ex)
                e = float(self.sub.evaluate(self.err_term,
                                            {"s": self.sign, "w": c}))
                if e < best:
                    best, bw = e, w
        return bw


# ==========================================================================
# THE TWO MANIFOLDS — built from the SAME train trajectories, LOSO. One exemplar
# per TRAIN speaker (its medoid token of the word) so the manifold spans the
# speaker space. The ENTANGLED manifold keeps raw (CMVN-only) trajectories; the
# SEPARABLE manifold factors EACH exemplar to ITS OWN speaker (content channel),
# so the DtwTo compares content-vs-content.
# ==========================================================================

def _medoid_per_speaker(trajs_by_speaker, K):
    """One representative trajectory per TRAIN speaker = its medoid token (closest to
    that speaker's mean), preserving the speaker's OWN dynamics. Cap at K speakers
    (fixed budget). A mechanical signal pick, no decision. Returns [raw_M, ...]."""
    reps = []
    for s, mats in trajs_by_speaker.items():
        if not mats:
            continue
        L = min(m.shape[0] for m in mats)
        stk = np.stack([m[:L] for m in mats], axis=0)
        mu = stk.mean(axis=0)
        d2 = ((stk - mu) ** 2).reshape(len(mats), -1).sum(axis=1)
        reps.append(mats[int(np.argmin(d2))])
    return reps[:K]


def build_manifolds(train_M, train_words, train_speakers, words, K):
    """Build BOTH manifolds from the SAME train medoids.
      entangled[w] = [ as_tuple(CMVN(raw)) ]            (no speaker channel)
      separable[w] = [ as_tuple(factor_out_speaker(raw)) ]  (each factored to its
                       OWN estimated speaker = content channel)
    Same exemplars, same speakers, same K — only the speaker-factoring differs."""
    by_ws = {}
    for M, w, s in zip(train_M, train_words, train_speakers):
        if M is None or M.shape[0] < 2:
            continue
        by_ws.setdefault(w, {}).setdefault(s, []).append(M)
    entangled, separable = {}, {}
    for w in words:
        reps = _medoid_per_speaker(by_ws.get(w, {}), K)
        entangled[w] = [as_tuple(cmvn(r, do_variance=True)) for r in reps]
        separable[w] = [as_tuple(factor_out_speaker(r, estimate_speaker(r)))
                        for r in reps]
    return entangled, separable


# ==========================================================================
# DATA LOADERS — return [(M_raw, word, speaker)] split train / test by SPEAKER.
# ==========================================================================

def _traj_M(x, fs):
    """Heard A1-patch trajectory matrix (frames x patches) — the same owned T10 the
    AbS path uses. None if the utterance is too short."""
    return traj_to_matrix(utterance_trajectory(x, fs))


def load_fsdd(n_per, K):
    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n_per])
    digits = ['zero', 'one', 'two', 'three', 'four', 'five',
              'six', 'seven', 'eight', 'nine']
    rows = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        rows.append((x, fs, digits[digit], sp))
    return rows, digits


def load_sc(n_words, n_per_word, n_test):
    """Google Speech Commands, split by SPEAKER (held-out-speaker test). Loads up to
    n_per_word train + however many test clips per word, decimated to 8 kHz (the
    cochlea's rate). Returns ([(M_raw,word,spk)], words)."""
    SC = RSP.SC
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append((os.path.join(SC, w, fn),
                                               fn.split("_")[0]))
    # hold out whole speakers
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train_paths = [(p, w, s) for w in words for p, s in data[w] if s not in test_spk]
    test_paths = [(p, w, s) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train_paths)
    random.shuffle(test_paths)
    # cap train per word to keep the medoid-per-speaker manifold tractable
    per_w = {}
    train_sel = []
    for p, w, s in train_paths:
        if per_w.get(w, 0) >= n_per_word:
            continue
        per_w[w] = per_w.get(w, 0) + 1
        train_sel.append((p, w, s))
    test_sel = test_paths[:n_test]
    rows_tr, rows_te = [], []
    for tag, paths, dst in (("tr", train_sel, rows_tr), ("te", test_sel, rows_te)):
        for i, (p, w, s) in enumerate(paths):
            x, fs = RSP.load_real(p)
            dst.append((x, fs, w, s))
    return rows_tr, rows_te, words


# ==========================================================================
# DRIVER
# ==========================================================================

def _extract(rows, tag):
    """rows [(x,fs,word,spk)] -> ([M_raw], [word], [spk]) via the owned A1 trajectory."""
    Ms, ws, ss = [], [], []
    for i, (x, fs, w, s) in enumerate(rows):
        Ms.append(_traj_M(x, fs))
        ws.append(w)
        ss.append(s)
        if (i + 1) % 100 == 0:
            print(f"  [{tag}] {i+1}/{len(rows)} trajectories", flush=True)
    return Ms, ws, ss


def main():
    t0 = time.time()
    venue = sys.argv[1] if len(sys.argv) > 1 else "sc"
    K = int(sys.argv[5]) if len(sys.argv) > 5 else 8     # fixed exemplar budget

    if venue == "fsdd":
        n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 6
        rows, words = load_fsdd(n_per, K)
        speakers = sorted(set(r[3] for r in rows))
        print(f"=== speaker_channel_drive  venue=FSDD  {len(rows)} recordings  "
              f"{len(speakers)} speakers  {len(words)} words  K={K} ===", flush=True)
        # FSDD: LOSO over the 6 speakers (each speaker held out in turn)
        all_M, all_w, all_s = _extract([(x, fs, w, s) for x, fs, w, s in rows], "all")
        chance = 1.0 / len(words)
        ent_c = ent_t = sep_c = sep_t = sh_c = sh_t = 0
        sub = Substrate()
        rec = Recogniser(sub, words)
        for held in speakers:
            tr = [i for i in range(len(all_s)) if all_s[i] != held]
            te = [i for i in range(len(all_s)) if all_s[i] == held]
            ent_man, sep_man = build_manifolds(
                [all_M[i] for i in tr], [all_w[i] for i in tr],
                [all_s[i] for i in tr], words, K)
            sh_man = _shuffle_manifold(sep_man)
            for i in te:
                M = all_M[i]
                if M is None or M.shape[0] < 2:
                    continue
                true = all_w[i]
                # (A) ENTANGLED: recognise on raw (CMVN-only) trajectory
                a = rec.match(as_tuple(cmvn(M, do_variance=True)), ent_man)
                # (B) SEPARABLE: estimate speaker, factor out, recognise on content
                slc = estimate_speaker(M)
                content = factor_out_speaker(M, slc)
                b = rec.match(as_tuple(content), sep_man)
                # shuffle control on (B)
                sh = rec.match(as_tuple(content), sh_man)
                if a is not None:
                    ent_c += int(a == true); ent_t += 1
                if b is not None:
                    sep_c += int(b == true); sep_t += 1
                if sh is not None:
                    sh_c += int(sh == true); sh_t += 1
            print(f"  held-out {held}: entangled {ent_c}/{ent_t}  "
                  f"separable {sep_c}/{sep_t}  shuffle {sh_c}/{sh_t}", flush=True)
        _report(ent_c, ent_t, sep_c, sep_t, sh_c, sh_t, chance, K, t0)
        return

    # ---- Google Speech Commands held-out-speaker (default venue) ----
    n_words = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    n_per_word = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    n_test = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    rows_tr, rows_te, words = load_sc(n_words, n_per_word, n_test)
    print(f"=== speaker_channel_drive  venue=SpeechCommands  train={len(rows_tr)}  "
          f"test={len(rows_te)} (HELD-OUT speakers)  {len(words)} words  K={K} ===",
          flush=True)
    print(f"words: {words}", flush=True)
    chance = 1.0 / len(words)

    print("--- extracting owned A1 trajectories (train) ---", flush=True)
    tr_M, tr_w, tr_s = _extract(rows_tr, "train")
    print("--- extracting owned A1 trajectories (test) ---", flush=True)
    te_M, te_w, te_s = _extract(rows_te, "test")

    sub = Substrate()
    rec = Recogniser(sub, words)

    print("--- building BOTH manifolds (entangled / separable), LOSO by construction "
          "(train speakers disjoint from test) ---", flush=True)
    ent_man, sep_man = build_manifolds(tr_M, tr_w, tr_s, words, K)
    sh_man = _shuffle_manifold(sep_man)

    print("\n--- DO-CONTRAST: (A) ENTANGLED vs (B) SEPARABLE speaker channel ---",
          flush=True)
    ent_c = ent_t = sep_c = sep_t = sh_c = sh_t = 0
    ent_pw, sep_pw = {}, {}
    for i in range(len(te_M)):
        M = te_M[i]
        if M is None or M.shape[0] < 2:
            continue
        true = te_w[i]
        # (A) ENTANGLED — raw trajectory, no separate speaker channel
        a = rec.match(as_tuple(cmvn(M, do_variance=True)), ent_man)
        # (B) SEPARABLE — estimate the speaker channel, factor it out, recognise on content
        slc = estimate_speaker(M)
        content = factor_out_speaker(M, slc)
        b = rec.match(as_tuple(content), sep_man)
        # SHUFFLE control on (B): permuted exemplar labels must collapse to chance
        sh = rec.match(as_tuple(content), sh_man)
        if a is not None:
            ent_c += int(a == true); ent_t += 1
            ent_pw.setdefault(true, [0, 0]); ent_pw[true][0] += int(a == true); ent_pw[true][1] += 1
        if b is not None:
            sep_c += int(b == true); sep_t += 1
            sep_pw.setdefault(true, [0, 0]); sep_pw[true][0] += int(b == true); sep_pw[true][1] += 1
        if sh is not None:
            sh_c += int(sh == true); sh_t += 1
        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(te_M)}: entangled {ent_c}/{ent_t}  "
                  f"separable {sep_c}/{sep_t}", flush=True)
    _report(ent_c, ent_t, sep_c, sep_t, sh_c, sh_t, chance, K, t0,
            ent_pw=ent_pw, sep_pw=sep_pw, words=words)


def _shuffle_manifold(manifold):
    """Permute the exemplar->word labels (control): pool all exemplars, re-deal them to
    words keeping per-word counts. If (B)'s gain survives this, it is an artifact."""
    pool = [ex for w in manifold for ex in manifold[w]]
    counts = {w: len(manifold[w]) for w in manifold}
    rng = random.Random(7)
    rng.shuffle(pool)
    out, j = {}, 0
    for w in manifold:
        out[w] = pool[j:j + counts[w]]
        j += counts[w]
    return out


def _report(ent_c, ent_t, sep_c, sep_t, sh_c, sh_t, chance, K, t0,
            ent_pw=None, sep_pw=None, words=None):
    ent_acc = ent_c / max(ent_t, 1)
    sep_acc = sep_c / max(sep_t, 1)
    sh_acc = sh_c / max(sh_t, 1)
    delta = sep_acc - ent_acc
    print("\n========================= DO-CONTRAST RESULT =========================",
          flush=True)
    print(f"  chance (1/n_words)                  : {chance:.4f}", flush=True)
    print(f"  (A) ENTANGLED  (no speaker channel) : {ent_acc:.4f}  ({ent_c}/{ent_t})",
          flush=True)
    print(f"  (B) SEPARABLE  (speaker channel)    : {sep_acc:.4f}  ({sep_c}/{sep_t})",
          flush=True)
    print(f"  DELTA (separable - entangled)       : {delta:+.4f}", flush=True)
    print(f"  SHUFFLE control on (B)              : {sh_acc:.4f}  ({sh_c}/{sh_t})  "
          f"[must be ~chance]", flush=True)
    if ent_pw and sep_pw and words:
        print("  per-word (entangled -> separable):", flush=True)
        for w in words:
            ea = ent_pw.get(w, [0, 0]); sa = sep_pw.get(w, [0, 0])
            if ea[1]:
                print(f"    {w:10s}: {ea[0]/ea[1]:.2f} -> {sa[0]/sa[1]:.2f}", flush=True)

    print("\n========================= VERDICT =========================", flush=True)
    shuffle_ok = sh_acc <= chance + 0.05
    if delta > 0.005 and shuffle_ok:
        print(f"  SEPARABLE CHANNEL HELPS: estimating the speaker as its own structure "
              f"and recognising on the factored-out content moved cross-speaker "
              f"recognition {delta:+.4f} ({ent_acc:.4f} -> {sep_acc:.4f}); the shuffle "
              f"control sits at chance ({sh_acc:.4f}) -> the gain is STRUCTURE, not an "
              f"artifact.", flush=True)
        verdict = "SEPARABLE_HELPS"
    elif delta > 0.005 and not shuffle_ok:
        print(f"  ARTIFACT: (B) beat (A) by {delta:+.4f} BUT the label-shuffle control "
              f"also rose to {sh_acc:.4f} (>> chance {chance:.4f}) -> the gain is an "
              f"artifact of the harness, NOT speaker-invariant structure. REJECT.",
              flush=True)
        verdict = "ARTIFACT_SHUFFLE_ROSE"
    elif abs(delta) <= 0.005:
        print(f"  HONEST NULL: the separable speaker channel did NOT beat the entangled "
              f"pipeline on this venue (delta {delta:+.4f}). The explicit-separate-channel "
              f"structure does not move cross-speaker recognition here — reported plainly, "
              f"NOT swept. Likely WHY: the speaker estimate (log-spectral centroid VTL "
              f"proxy) is too BLURRY on this front-end to cleanly factor the talker out "
              f"(the gammatone-wall bound the prior speaker work hit), and/or the residual "
              f"cross-speaker variance is NOT a single VTL scale (formant pattern, rate, "
              f"channel) that one centroid-warp removes.", flush=True)
        verdict = "HONEST_NULL"
    else:
        print(f"  SEPARABLE CHANNEL HARMS: the separate channel LOWERED recognition "
              f"{delta:+.4f}. Factoring the (blurry) speaker estimate out removed phonetic "
              f"content too -> the estimate is not clean enough to separate. Reported "
              f"plainly.", flush=True)
        verdict = "SEPARABLE_HARMS"

    print(f"\nVERDICT_TOKEN={verdict}  delta={delta:+.4f}  entangled={ent_acc:.4f}  "
          f"separable={sep_acc:.4f}  shuffle={sh_acc:.4f}  chance={chance:.4f}  K={K}",
          flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()

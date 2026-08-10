"""analysis_by_synthesis_accept — recognition by INVERTING the forward model.

THE MISSING STRUCTURAL COMPONENT (docs/speech_development_missing_component.md):
the agent owns every piece of analysis-by-synthesis (AxS) — a forward model
(STTPipeline.speak / synthesize_from_trajectory in the heard voice), a
speaker-invariant front-end, DTW, a candidate lexicon — but the generator only
ever pointed OUTWARD (talking / self-monitoring). It was never run in reverse to
PERCEIVE. This wires it:

    recognise(s) = argmax_w  -synth_error(s, w)
    synth_error(s, w) = DTW( features(s), features( speak(w | voice(s)) ) )

For a heard sign s: synthesise each candidate word w in s's OWN voice (f0
estimated from s), front-end it with the SAME invariant transform the bottom-up
path uses, DTW it to features(s); the word whose synthesis best predicts the
input wins. This compares instance<->CANONICAL-SYNTHESIS (not
instance<->instance), so speaker/coarticulation nuisance is absorbed into the
forward model and the residual error is dominated by phonetic identity — the
structural reason it should beat feature-matching cross-speaker.

ARCHITECTURE (honest split, per the task):
  - The DTW distance kernel is a NEW Rust DSL Term: `DtwTo` (synthesis+compare is
    inexpressible from existing Terms). Specified via runtime_design
    (agent_specify_synth_error), emitted by the mechanical generator, integrated
    in runners/dsl/src/term.rs.
  - Synthesis stays at the I/O boundary: this adapter calls
    speak_trajectory() in voice(s), front-ends it, writes the result onto the
    candidate word as a graph attr.
  - The DECISION — argmax over candidates of -DtwTo(features(s), synth(w)) — is
    composed and evaluated in the GRAPH (recognition_graph.predict_synth_term).

FORWARD MODEL (honest): speak() over the trained lexicon collapses (one mega-sign
denotes all words), so we build the word->sound forward model directly as the
MEAN per-utterance A1-patch trajectory of each word's TRAIN-speaker exemplars
(LOSO — the held-out speaker never contributes to its own forward model). That is
exactly the doc's "speak(w) voices the stored trajectory of word w", built
cleanly rather than through the collapsed matcher. This is the project's #3
follow-on (production-calibrate the forward model) done as a simple exemplar
average; AxS quality is bounded by it (caveat #1).

REPRESENTATION (honest, measured): we compare the heard utterance's A1-patch
trajectory to the forward model's per-word mean A1 trajectory IN THE MODEL'S OWN
REPRESENTATION (instance<->model). Resynthesising to AUDIO and re-running the
gammatone front-end injects a natural-vs-synthetic DOMAIN GAP (~6.8 constant DTW
offset) that swamps the phonetic residual — exactly caveat #1 (speak() quality
bounds AxS). Comparing in the forward model's native A1 space avoids that gap and
is the faithful AxS form (the brain inverts the internal forward model, it does
not literally play sound and re-hear it). The audio-resynthesis path is kept as a
secondary measure to SHOW the domain-gap bound. Both go through the graph DtwTo
Term + predict_synth_term argmax.

MEASURES (all LIVE):
  1. FSDD digits, held-out speakers (LOSO): AxS vs the bottom-up baseline.
  2. THE STRUCTURAL TEST — cross-speaker same-word 2AFC (true vs distractor).
  3. Shuffle control — AxS must collapse to chance.

Run: python -m scripts.analysis_by_synthesis_accept [n_per_speaker_per_digit]
"""
import sys
import math
import random
import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _estimate_f0
from domains.invariant_units import invariant_transform, canonical_log_centroid
from domains import recognition_graph as RG
from domains import runtime_design as RD
from scripts.invariant_units_accept import band_trajectory_matrix, dtw
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def feats(x, fs, canonical):
    """The shared invariant front-end: gammatone band trajectory -> forward-VTLN +
    CMVN. The SAME transform on heard audio AND synthesised audio, so AxS compares
    like with like."""
    return invariant_transform(band_trajectory_matrix(x, fs), canonical)


def as_tuple(M):
    """frames x bands numpy -> nested Python tuples for a graph attr / DtwTo."""
    return tuple(tuple(float(v) for v in row) for row in M)


_N_PATCHES = 25   # A1 patch count; A1 trajectory = spp * n_patches


def utterance_trajectory(x, fs):
    """One utterance's A1-patch trajectory, extracted by ingesting into a FRESH
    substrate (so the lexical matcher can't collapse it into a shared sign). The
    word-distinct building block of the word->sound forward model."""
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    pipe.ingest(sub, x)
    sub.tick(50000)
    best = None
    for s in sub.nodes("AcousticSign"):
        t = sub.node(s)["attrs"].get("trajectory")
        if t and (best is None or len(t) > len(best)):
            best = t
    return np.array([float(v) for v in best], dtype=np.float32) if best else None


def traj_to_matrix(t, n_patches=_N_PATCHES):
    """A1 trajectory (flat spp*n_patches) -> frames x patches matrix for DtwTo."""
    if t is None:
        return None
    spp = len(t) // n_patches
    if spp == 0:
        return None
    return t[:spp * n_patches].reshape(spp, n_patches).astype(np.float32)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n])
    speakers = sorted(set(it[2] for it in items))
    print(f"FSDD: {len(items)} recordings, {len(speakers)} speakers, 10 digits")

    loaded = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        loaded.append((x, fs, digit, sp))
    fs = loaded[0][1]

    raw_M = [band_trajectory_matrix(x, fs) for x, fs, _, _ in loaded]
    canonical = canonical_log_centroid(raw_M)
    inv_M = [invariant_transform(M, canonical) for M in raw_M]
    words = [_DIGITS[d] for _, _, d, _ in loaded]
    spks = [s for _, _, _, s in loaded]
    print(f"cohort canonical log-centroid (VTLN ref): {canonical:.4f} "
          f"(= {math.exp(canonical):.0f} Hz)")

    # ---- bottom-up baseline: instance<->instance 1-NN DTW, LOSO ----
    def loso_1nn_dtw(mats):
        corr = tot = 0
        per_word = {}
        for held in sorted(set(spks)):
            te = [i for i, s in enumerate(spks) if s == held]
            tr = [i for i, s in enumerate(spks) if s != held]
            for i in te:
                best, bw = 1e18, None
                for j in tr:
                    d = dtw(mats[i], mats[j])
                    if d < best:
                        best, bw = d, words[j]
                ok = int(bw == words[i])
                corr += ok
                tot += 1
                per_word.setdefault(words[i], [0, 0])
                per_word[words[i]][0] += ok
                per_word[words[i]][1] += 1
        return corr / max(tot, 1), per_word

    print("\n--- BOTTOM-UP baseline (instance<->instance 1-NN DTW, LOSO) ---")
    bu_acc, bu_pw = loso_1nn_dtw(inv_M)
    print(f"bottom-up LOSO 1-NN DTW acc: {bu_acc:.3f}")

    # ---- build the word->sound FORWARD MODEL: per-utterance A1 trajectories ----
    print("\n--- building forward model (per-utterance A1 trajectories) ---")
    utt_traj = [utterance_trajectory(x, fs) for x, fs, _, _ in loaded]
    have = sum(1 for t in utt_traj if t is not None)
    print(f"extracted {have}/{len(loaded)} clean per-utterance trajectories")

    # A substrate with the A1 patch layout so speak_trajectory can read it.
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    # Ingest one utterance to mint the A1Patch nodes the synth needs.
    pipe.ingest(sub, loaded[0][0])
    sub.tick(50000)
    print(f"A1 patches in synth substrate: "
          f"{sum(1 for _ in sub.nodes('A1Patch'))}")

    # The agent SPECIFIES the new primitive (runtime_design) — honest record.
    spec = RD.agent_specify_synth_error(sub)
    print(f"agent_specify_synth_error: name={spec['name']} "
          f"kind={spec['semantic_kind']}")
    emitted = RD.emit_primitive_rust(spec)
    print(f"  mechanical generator emitted Rust across {len(emitted)} "
          f"TermNode homes (DtwTo).")

    RG.mark_words(sub, _DIGITS)
    word_concept = {}
    for w in _DIGITS:
        c = next((c for c in sub.nodes("Concept")
                  if sub.node(c)["attrs"].get("name") == w), None)
        if c is None:
            c = sub.add_node("Concept", {"name": w, "origin": "axs"})
            sub.set_attr(c, RG.WORD_ATTR, 1.0)
        word_concept[w] = c

    sign_node = sub.add_node("AcousticSign", {"axs_probe": 1.0})
    pred_term = _Pred(RG.predict_synth_term())

    def fwd_traj(word, held_speaker):
        """word->sound forward model: mean per-utterance A1 trajectory over
        TRAIN-speaker exemplars of `word` (LOSO — exclude held_speaker)."""
        ts = [utt_traj[i] for i, (x, fs, d, s) in enumerate(loaded)
              if _DIGITS[d] == word and s != held_speaker
              and utt_traj[i] is not None]
        if not ts:
            return None
        L = min(len(t) for t in ts)
        return np.mean([t[:L] for t in ts], axis=0)

    # Forward-model per-word mean A1 trajectory, cached per held speaker (LOSO).
    fwd_cache = {}

    def model_feats(word, held_speaker):
        """The forward model's per-word features in its NATIVE A1 representation —
        the faithful AxS comparison target (instance<->model, no resynthesis
        domain gap). Returns frames x patches tuple for DtwTo."""
        key = (word, held_speaker)
        if key not in fwd_cache:
            M = traj_to_matrix(fwd_traj(word, held_speaker))
            fwd_cache[key] = as_tuple(M) if M is not None else None
        return fwd_cache[key]

    # Audio-resynthesis features (secondary measure; shows the domain-gap bound).
    synth_cache = {}

    def synth_feats(word, held_speaker, f0):
        bucket = int(round(f0 / 15.0)) if f0 > 0 else 0
        key = (word, held_speaker, bucket)
        if key in synth_cache:
            return synth_cache[key]
        tr = fwd_traj(word, held_speaker)
        if tr is None:
            synth_cache[key] = None
            return None
        audio = pipe.speak_trajectory(sub, tr, duration_s=0.4,
                                      f0_hz=(f0 if f0 > 0 else None))
        if audio is None or np.abs(audio).max() < 1e-4:
            synth_cache[key] = None
            return None
        synth_cache[key] = as_tuple(feats(audio, fs, canonical))
        return synth_cache[key]

    # ---- AxS recognition (LOSO, graph DtwTo argmax, native A1 representation) --
    print("\n--- ANALYSIS-BY-SYNTHESIS recognition (graph decision, LOSO) ---")
    axs_corr = axs_tot = 0
    axs_pw = {}
    decisions = []
    for i, (x, _fs, digit, sp) in enumerate(loaded):
        true_w = _DIGITS[digit]
        f0 = _estimate_f0(x, fs)
        heardM = traj_to_matrix(utt_traj[i])
        if heardM is None:
            continue
        heard = as_tuple(heardM)
        sub.set_attr(sign_node, RG.SIGN_FEAT_ATTR, heard)
        ok_all = True
        for w, c in word_concept.items():
            mf = model_feats(w, sp)   # LOSO: forward model excludes sp
            if mf is None:
                ok_all = False
                break
            sub.set_attr(c, RG.WORD_FEAT_ATTR, mf)
        if not ok_all:
            continue
        pred = sub.evaluate(pred_term, {"s": sign_node})   # graph argmax of -DtwTo
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        ok = int(pw == true_w)
        axs_corr += ok
        axs_tot += 1
        axs_pw.setdefault(true_w, [0, 0])
        axs_pw[true_w][0] += ok
        axs_pw[true_w][1] += 1
        decisions.append((true_w, pw, heard, f0, sp))
    axs_acc = axs_corr / max(axs_tot, 1)
    print(f"AxS LOSO recognition acc (native A1, graph DtwTo): "
          f"{axs_acc:.3f}  ({axs_corr}/{axs_tot})")

    # Secondary: audio-resynthesis AxS — exposes the natural-vs-synthetic gap.
    rsc = rst = 0
    for i, (x, _fs, digit, sp) in enumerate(loaded):
        true_w = _DIGITS[digit]
        f0 = _estimate_f0(x, fs)
        sub.set_attr(sign_node, RG.SIGN_FEAT_ATTR, as_tuple(feats(x, fs, canonical)))
        bad = False
        for w, c in word_concept.items():
            sf = synth_feats(w, sp, f0)
            if sf is None:
                bad = True
                break
            sub.set_attr(c, RG.WORD_FEAT_ATTR, sf)
        if bad:
            continue
        pred = sub.evaluate(pred_term, {"s": sign_node})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        rsc += int(pw == true_w)
        rst += 1
    print(f"AxS LOSO acc (audio-resynthesis path): {rsc/max(rst,1):.3f}  "
          f"<- bounded by the natural/synthetic domain gap (caveat #1)")

    print(f"\n{'digit':>8s}{'bottom-up':>11s}{'AxS':>8s}")
    for w in _DIGITS:
        b = bu_pw.get(w, [0, 1])
        a = axs_pw.get(w, [0, 1])
        print(f"{w:>8s}{b[0]/max(b[1],1):>11.2f}{a[0]/max(a[1],1):>8.2f}")

    # ---- SHUFFLE control ----
    print("\n--- SHUFFLE control (synth feature<->word labels permuted) ---")
    rng = random.Random(0)
    perm = list(_DIGITS)
    rng.shuffle(perm)
    label_map = dict(zip(_DIGITS, perm))
    sh_corr = sh_tot = 0
    for true_w, _pw, heard, f0, sp in decisions:
        sub.set_attr(sign_node, RG.SIGN_FEAT_ATTR, heard)
        bad = False
        for w, c in word_concept.items():
            mf = model_feats(label_map[w], sp)   # mis-pointed forward model
            if mf is None:
                bad = True
                break
            sub.set_attr(c, RG.WORD_FEAT_ATTR, mf)
        if bad:
            continue
        pred = sub.evaluate(pred_term, {"s": sign_node})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        sh_corr += int(pw == true_w)
        sh_tot += 1
    print(f"AxS acc under shuffle: {sh_corr/max(sh_tot,1):.3f} "
          f"(chance 0.10 — must collapse)")

    # ---- THE STRUCTURAL TEST: cross-speaker 2AFC ----
    print("\n--- STRUCTURAL TEST: cross-speaker 2AFC (true vs distractor) ---")

    err_term = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), RG.SIGN_FEAT_ATTR),
                               RG._Attr(RG._V("w"), RG.WORD_FEAT_ATTR)))

    def axs_err(heard, w, sp, f0):
        mf = model_feats(w, sp)   # native A1 forward model (no domain gap)
        if mf is None:
            return None
        sub.set_attr(sign_node, RG.SIGN_FEAT_ATTR, heard)
        c = word_concept[w]
        sub.set_attr(c, RG.WORD_FEAT_ATTR, mf)
        return float(sub.evaluate(err_term, {"s": sign_node, "w": c}))

    wins = trials = 0
    for true_w, _pw, heard, f0, sp in decisions:
        for dist in _DIGITS:
            if dist == true_w:
                continue
            e_true = axs_err(heard, true_w, sp, f0)
            e_dist = axs_err(heard, dist, sp, f0)
            if e_true is None or e_dist is None:
                continue
            wins += int(e_true < e_dist)
            trials += 1
    axs_2afc = wins / max(trials, 1)
    print(f"AxS cross-speaker 2AFC (true word beats distractor): "
          f"{axs_2afc:.3f}  (chance 0.50)")

    # bottom-up cross-speaker 2AFC: same-word other-speaker NN vs other-word.
    by_word_spk = {}
    for idx, (x, _fs, d, s) in enumerate(loaded):
        by_word_spk.setdefault((_DIGITS[d], s), []).append(idx)

    bwins = btrials = 0
    for i, (x, _fs, d, s) in enumerate(loaded):
        tw = _DIGITS[d]
        same = [j for (ww, ss), js in by_word_spk.items()
                if ww == tw and ss != s for j in js]
        for dist_w in _DIGITS:
            if dist_w == tw:
                continue
            diff = [j for (ww, ss), js in by_word_spk.items()
                    if ww == dist_w and ss != s for j in js]
            if not same or not diff:
                continue
            d_true = min(dtw(inv_M[i], inv_M[j]) for j in same)
            d_dist = min(dtw(inv_M[i], inv_M[j]) for j in diff)
            bwins += int(d_true < d_dist)
            btrials += 1
    bu_2afc = bwins / max(btrials, 1)
    print(f"bottom-up cross-speaker 2AFC (same-word NN beats other-word NN): "
          f"{bu_2afc:.3f}  (chance 0.50)")

    print("\n===============================================")
    print("ANALYSIS-BY-SYNTHESIS — summary")
    print("===============================================")
    print(f"bottom-up LOSO 1-NN DTW acc:       {bu_acc:.3f}  "
          f"(uses ALL train exemplars as NN candidates)")
    print(f"AxS LOSO acc (native A1, graph):   {axs_acc:.3f}  "
          f"(ONE forward model per word — instance<->model)")
    print(f"AxS LOSO acc (audio-resynth path): {rsc/max(rst,1):.3f}  "
          f"(bounded by natural/synthetic domain gap — caveat #1)")
    print(f"AxS acc under shuffle:             {sh_corr/max(sh_tot,1):.3f} "
          f"(chance 0.10 — collapses, control holds)")
    print(f"AxS cross-speaker 2AFC:            {axs_2afc:.3f} (chance 0.50)")
    print(f"bottom-up cross-speaker 2AFC:      {bu_2afc:.3f} (chance 0.50)")


if __name__ == "__main__":
    main()

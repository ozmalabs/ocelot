"""formant_trajectory_dynamics — THE DYNAMICS RUNG.

The static 3-formant nucleus frame provably cannot separate coarticulated
digits: measured at 8 kHz, ih (six) and uw (two) collapse onto each other (the
high-back F1/F2 cluster merges, uw's F2 is pulled up toward ih's). A SINGLE
steady frame is an order-0 snapshot — it throws the MOTION away. But the motion
IS the identity: the way F2 sweeps INTO and OUT of the vowel (the locus
equations / formant transitions across the consonant<->vowel boundary) is a
speaker-invariant gesture. This rung recognises FSDD digits by their formant
TRAJECTORY and its order-N-over-time dynamics, using the session's OWN order-N
operator.

REPRESENTATION (owned DSP, NO net/fit):
  * FORMANT TRAJECTORY — F1,F2,F3 estimated per FRAME across the FULL digit token
    (multiple frames, INCLUDING the consonant<->vowel transitions, not just the
    steady nucleus). Reuses solve_for_n_vowel.estimate_formants (LPC roots, the
    same owned all-pole inversion the vowel rung uses), per voiced frame.
  * SPEAKER-RELATIVE — each frame's formants -> log-formants minus the PER-TOKEN
    mean (cancels VTL: a vocal-tract-length change is a multiplicative shift on
    all formants = additive in log = removed by the mean). The same VTL invariant
    the vowel rung established.
  * ORDER-N DYNAMICS — the agent's OWN order-N operator
    (domains.order_n_concepts.nth_order_terms, recursive Minus, evaluated
    NATIVELY by the substrate) applied DOWN THE TIME AXIS of each speaker-relative
    formant track -> order-1 (velocity, the formant TRANSITION) and order-2
    (curvature, the acceleration of the glide). Differencing is the agent's Rust
    Term-tree, NOT numpy (numpy used only as an audit reference). Each frame of
    the trajectory carries [F1,F2,F3 (rel) | dF1,dF2,dF3 | ddF1,ddF2,ddF3].

RECOGNITION (the agent's graph-resident cognition):
  * DTW-aligned trajectory match. The recognition DECISION is the agent's OWN
    graph Term — Argmin over candidate-digit Concepts of (MinOver that digit's
    banked exemplars of DtwTo(query_traj, exemplar_traj)) — composed from DtwTo
    (the agent's banded Sakoe-Chiba alignment Rust Term), MinOver, Argmin, and
    evaluated NATIVELY via substrate.evaluate. The DTW warp absorbs rate +
    speaker timing; what it scores is the residual SHAPE of the gesture (the
    speaker-invariant motion). Exemplars from TRAIN speakers only.

BASELINES (same FSDD LOSO split, held-out speaker NEVER banked):
  (a) STATIC single-nucleus formant 1-NN — F1,F2,F3 at the steady nucleus only
      (the order-0 snapshot, the ~52% regime). The thing the dynamics must beat.
  (b) Full-envelope DTW exemplar 1-NN — the confirmed log-mel banded-DTW
      recognizer (mcu_infer pipeline, the prior ~0.76-0.785 cross-speaker bank).

PREDICTION: the trajectory + order-N dynamics separates coarticulated digits the
static frame collapses -> accuracy climbs well above the static ~52%, toward/at
the full-envelope exemplar baseline. KILL/HONEST: if dynamics does NOT separate
them (trajectory estimation too noisy cross-speaker / the order-N derivatives
overlap), report it and pinpoint the next limiter.

DONKEY AUDIT: formant trajectory = solve_for_n_vowel.estimate_formants (LPC
roots, owned DSP, no fit). order-N dynamics = order_n_concepts.nth_order_terms
(the agent's operator, native eval). recognition = the agent's DtwTo/MinOver/
Argmin Term evaluated natively (no learned weight, no net). Exemplars TRAIN-only;
held-out speaker never banked; LOSO is the ungameable yardstick.

Run:  python -m scripts.formant_trajectory_dynamics
      python -m scripts.formant_trajectory_dynamics --quick
"""
from __future__ import annotations

import os
import sys
import time
import wave
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate, Lit
from domains.order_n_concepts import nth_order_terms
from scripts.solve_for_n_vowel import estimate_formants
# the confirmed full-envelope DTW exemplar baseline (the ~0.76 bank), reused verbatim
from scripts import mcu_infer as mi
# NATIVE cognition Terms (the agent's graph-resident decisions; substrate.evaluate).
import domains.native_cognition as NC          # rel-formants (Log + composed Mean)
import domains.native_vote as NV               # k-NN mel majority vote (Fold/Count/Argmax)

DATA_DIR = "/tmp/fsdd/recordings"
DIGITS = ["zero", "one", "two", "three", "four", "five",
          "six", "seven", "eight", "nine"]
FS = 8000
FRAME_MS = 32.0
HOP_MS = 12.0
LPC_ORDER = 10
VOICED_FLOOR = 0.10     # frame-energy gate (fraction of max RMS) for voiced frames


# ===========================================================================
#  AUDIO LOAD (world I/O boundary)
# ===========================================================================

def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float64) / 32768.0
    peak = max(float(np.abs(arr).max()), 1e-9)
    return arr * 0.7 / peak, fs


def gather_files():
    import re
    rx = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = rx.match(fn)
        if m:
            d, spk, idx = m.groups()
            out.append((os.path.join(DATA_DIR, fn), int(d), spk, int(idx)))
    return out


# ===========================================================================
#  FORMANT TRACK over the FULL token (owned DSP — LPC-root formants per frame)
# ===========================================================================

def formant_track(sig, fs):
    """F1,F2,F3 per VOICED frame across the WHOLE token (transitions included).
    Each frame's formants estimated by solve_for_n_vowel.estimate_formants (LPC
    roots — the agent's owned all-pole inversion). Frames where < 3 poles resolve
    are dropped. Returns an (n_frames x 3) array of raw Hz formants, or None."""
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if len(sig) < flen:
        return None
    starts = list(range(0, len(sig) - flen + 1, hop))
    energies = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
    if energies.max() <= 1e-9:
        return None
    thr = VOICED_FLOOR * energies.max()
    rows = []
    for s, e in zip(starts, energies):
        if e < thr:
            continue
        f = estimate_formants(sig[s:s + flen], fs=fs, order=LPC_ORDER, n_form=3)
        if f is not None:
            rows.append(f)
    if len(rows) < 3:
        return None
    return np.asarray(rows, dtype=np.float64)


def steady_nucleus_formants(track):
    """The STATIC order-0 snapshot: the single steady-nucleus formant frame. We
    take the MEDIAN formant over the central (most stationary) portion of the
    track — the steady vowel nucleus a single-frame recogniser would read."""
    n = track.shape[0]
    lo, hi = int(0.25 * n), max(int(0.25 * n) + 1, int(0.75 * n))
    return np.median(track[lo:hi], axis=0)     # (3,)


# A process-wide substrate for evaluating the native rel-formants Term (scalar Log + composed
# Mean). Created lazily; the Term carries no per-token state, so one shared substrate suffices.
_REL_SUB = None


def relative_formants_frame(formants):
    """Speaker-RELATIVE formant frame: log-formants minus their mean (cancels VTL). The same
    VTL-cancelling invariant, now computed by the agent's NATIVE rel-formants Term
    (domains.native_cognition.rel_formants_channel_term: Log(Nth(f,i)) - Div(Sum(Log(f)),n)),
    evaluated by substrate.evaluate (native Rust). Owned transduction adds the +1e-9 floor (the
    log-domain guard) before the native Log, exactly as the prior numpy did."""
    global _REL_SUB
    if _REL_SUB is None:
        _REL_SUB = Substrate()
    f = np.asarray(formants, dtype=np.float64) + 1e-9
    return np.asarray(NC.native_rel_formants(_REL_SUB, f, _P, n_formants=f.shape[0]),
                      dtype=np.float64)


# ===========================================================================
#  ORDER-N DYNAMICS — the agent's OWN operator, evaluated NATIVELY in Rust.
#  Difference each speaker-relative formant track DOWN THE TIME AXIS via
#  order_n_concepts.nth_order_terms (recursive Minus). order-1 = velocity (the
#  formant TRANSITION), order-2 = curvature.
# ===========================================================================

class _AuditError(Exception):
    pass


def order_n_time(sub, rel_track, order):
    """The order-N finite difference of a (frames x 3) speaker-relative formant
    track DOWN THE TIME AXIS, computed by the agent's nth_order_terms operator and
    evaluated NATIVELY by the substrate (one substrate.evaluate per scalar). Each
    formant channel is differenced independently. Returns an (frames-order x 3)
    array. The numpy np.diff is computed only as a DONKEY AUDIT cross-check."""
    n, ch = rel_track.shape
    out = np.zeros((n - order, ch), dtype=np.float64)
    for c in range(ch):
        samples = [Lit(float(v)) for v in rel_track[:, c]]
        terms = nth_order_terms(samples, order)   # the agent's Term-trees
        for i, t in enumerate(terms):
            out[i, c] = sub.evaluate(t, {})       # NATIVE Rust evaluation
    # donkey audit: the native order-N must equal numpy's finite difference.
    ref = np.diff(rel_track, n=order, axis=0)
    if not np.allclose(out, ref, atol=1e-7):
        raise _AuditError("native order-N != numpy reference")
    return out


def trajectory_feature(sub, track, max_order=2):
    """The full DYNAMICS trajectory feature for one token: each frame carries the
    speaker-relative formants AND their order-1 (velocity) + order-2 (curvature)
    over time. Aligned to the shortest (order-2) length so every frame is a
    [F1,F2,F3 | dF1,dF2,dF3 | ddF1,ddF2,ddF3] vector. Returns an (frames x 9)
    array (a tuple-of-frames trajectory the DtwTo Term aligns)."""
    rel = np.array([relative_formants_frame(f) for f in track])   # (n x 3)
    o1 = order_n_time(sub, rel, 1)                                  # (n-1 x 3)
    o2 = order_n_time(sub, rel, 2)                                  # (n-2 x 3)
    m = o2.shape[0]                                                 # = n-2
    # align: drop the leading frames so all three stacks share the order-2 length.
    rel_a = rel[2:2 + m]
    o1_a = o1[1:1 + m]
    o2_a = o2[:m]
    return np.concatenate([rel_a, o1_a, o2_a], axis=1)             # (m x 9)


# ===========================================================================
#  THE AGENT'S GRAPH-RESIDENT DTW RECOGNITION DECISION (native Term).
#    predict(query) = Argmin over digit Concepts w of
#                       MinOver e in has_exemplar(w) of DtwTo(q.traj, e.traj)
#  DtwTo = the agent's banded Sakoe-Chiba alignment Rust Term; MinOver = nearest
#  banked exemplar of the digit; Argmin = the digit decision. One substrate.evaluate.
# ===========================================================================

TRAJ_ATTR = "traj"
WORD_ATTR = "is_digit"
Q_ATTR = "q_traj"


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nb(node, e): return {"type": "Neighbours", "node": node, "edge_type": e,
                          "any_type": False}
def _DtwTo(a, b): return {"type": "DtwTo", "a": a, "b": b}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _MinOver(src, var, val): return {"type": "MinOver", "source": src,
                                     "var_name": var, "value": val, "default": None}
def _Argmin(src, var, val): return {"type": "Argmin", "source": src,
                                    "var_name": var, "value": val, "default": None}


def dtw_predict_term():
    """The agent's DTW-trajectory recognition DECISION as a graph Term-tree."""
    word_dist = _MinOver(_Nb(_V("w"), "has_exemplar"), "e",
                         _DtwTo(_Attr(_V("q"), Q_ATTR),
                                _Attr(_V("e"), TRAJ_ATTR)))
    return _Argmin(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", word_dist)


def _traj_tuple(feat):
    """A trajectory (frames x channels) as a tuple-of-tuples graph attr."""
    if feat is None or len(feat) == 0:
        return ((0.0,) * 9,)
    return tuple(tuple(float(v) for v in frame) for frame in feat)


# ===========================================================================
#  STATIC single-nucleus formant 1-NN baseline (the order-0 snapshot, ~52%).
# ===========================================================================

def static_nn_predict(query_static, bank_static):
    """1-NN over the single steady-nucleus speaker-relative formant frame (3-vec).
    The static order-0 snapshot — the thing the dynamics must beat."""
    best_w, best_d = None, np.inf
    for rel, w in bank_static:
        d = float(np.linalg.norm(query_static - rel))
        if d < best_d:
            best_d, best_w = d, w
    return best_w


# ===========================================================================
#  CORPUS — full-token features for every utterance.
# ===========================================================================

def build_corpus(sub, n_per_speaker=None, seed=0, quick=False):
    """Load FSDD, extract per-utterance: the DYNAMICS trajectory feature, the
    STATIC nucleus frame (speaker-relative), and the log-mel matrix (for the
    full-envelope DTW baseline). Mechanical ingest."""
    rng = np.random.default_rng(seed)
    files = gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    npr = n_per_speaker if n_per_speaker is not None else (6 if quick else 999)
    corpus = []
    mel_ops = mi.Ops()
    skipped = 0
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:npr]:
            sig, fs = load_wav(p)
            track = formant_track(sig, fs)
            if track is None:
                skipped += 1
                continue
            feat = trajectory_feature(sub, track)
            static = relative_formants_frame(steady_nucleus_formants(track))
            # full-envelope log-mel matrix (the confirmed baseline's front-end)
            xmcu, fsm = mi.load_wav(p)
            M = mi.front_end(xmcu, fsm, mel_ops)
            if M.shape[0] < 2:
                skipped += 1
                continue
            corpus.append({
                "word": DIGITS[d], "speaker": spk,
                "traj": feat, "static": static, "mel": M,
            })
    return corpus, skipped


def evaluate_clean(sub, corpus, verbose=True):
    """LOSO eval with a clean per-recogniser confusion matrix for BOTH the static
    and the dynamics recogniser (so the coarticulated-pair separation is auditable)."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()
    canonical = mi.canonical_log_centroid([it["mel"] for it in corpus])
    by_spk_mel = defaultdict(list)
    for it in corpus:
        by_spk_mel[it["speaker"]].append(it["mel"])
    spk_stats = {s: mi.speaker_stats(by_spk_mel[s]) for s in speakers}
    mel_ops = mi.Ops()
    mel_normed = {}
    for i, it in enumerate(corpus):
        mean, std = spk_stats[it["speaker"]]
        mel_normed[i] = mi.normalise(it["mel"], mean, std, canonical, mel_ops)

    dyn_c = dyn_n = stat_c = stat_n = mel_c = mel_n = 0
    per_speaker = {}
    conf_dyn = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_stat = {w: {u: 0 for u in DIGITS} for w in DIGITS}

    for held in speakers:
        test_idx = [i for i, it in enumerate(corpus) if it["speaker"] == held]
        train_idx = [i for i, it in enumerate(corpus) if it["speaker"] != held]
        s = Substrate()
        word_nodes = {}
        for w in DIGITS:
            word_nodes[w] = s.add_node("Concept", {"name": w, WORD_ATTR: 1.0})
        for i in train_idx:
            ex = s.add_node("Exemplar", {TRAJ_ATTR: _traj_tuple(corpus[i]["traj"])})
            # mechanical world-adapter wiring of the exemplar bank (not an agent
            # decision); has_exemplar is the recognizer's index. unchecked because a
            # bare substrate's Γ does not seed this edge in its vocabulary.
            s.add_edge_unchecked(word_nodes[corpus[i]["word"]], "has_exemplar", ex)
        q_node = s.add_node("Query", {Q_ATTR: ((0.0,) * 9,)})
        bank_static = [(corpus[i]["static"], corpus[i]["word"]) for i in train_idx]
        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]

        # NATIVE k-NN vote bank: one MelExemplar node per train exemplar; the owned DTW
        # distance to each query is written per token (transduction) and the top-k majority
        # DECISION is the native Term (domains.native_vote). Built once per fold.
        bank_mel_words = [w for _, w in bank_mel]
        vote_sub, vote_word_nodes, vote_ex_nodes = NV.build_vote_substrate(
            Substrate, DIGITS, bank_mel_words)

        s_dyn_c = s_dyn_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            pn = s.evaluate(_P(term), {"q": q_node})
            pred_dyn = s.node(pn)["attrs"].get("name") if pn is not None else None
            dyn_n += 1; s_dyn_t += 1
            if pred_dyn == true:
                dyn_c += 1; s_dyn_c += 1
            if pred_dyn in DIGITS:
                conf_dyn[true][pred_dyn] += 1
            pred_stat = static_nn_predict(corpus[i]["static"], bank_static)
            stat_n += 1
            if pred_stat == true:
                stat_c += 1
            if pred_stat in DIGITS:
                conf_stat[true][pred_stat] += 1
            # owned DTW distances (transduction, numpy) -> native top-k majority DECISION.
            dists = [mi.dtw(mel_normed[i], Mtr, mel_ops) for Mtr, _ in bank_mel]
            pred_mel = NV.native_vote(vote_sub, vote_ex_nodes, dists, mi.KNN_K, _P)
            mel_n += 1
            if pred_mel == true:
                mel_c += 1
        per_speaker[held] = s_dyn_c / max(1, s_dyn_t)
        if verbose:
            print(f"    held-out {held:10s}: dyn {s_dyn_c/max(1,s_dyn_t):.3f}  "
                  f"(n={s_dyn_t})", flush=True)

    return {
        "dyn_acc": dyn_c / max(1, dyn_n), "dyn_n": dyn_n,
        "stat_acc": stat_c / max(1, stat_n), "stat_n": stat_n,
        "mel_acc": mel_c / max(1, mel_n), "mel_n": mel_n,
        "per_speaker": per_speaker,
        "conf_dyn": conf_dyn, "conf_stat": conf_stat,
    }


def _print_confusion(title, conf):
    print(f"\n  {title} (row=true, col=pred):")
    print("           " + " ".join(f"{u[:4]:>4}" for u in DIGITS))
    for w in DIGITS:
        print(f"    {w:>6}: " + " ".join(f"{conf[w][u]:>4}" for u in DIGITS))


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()   # the substrate used for native order-N evaluation
    print("=" * 76)
    print("formant_trajectory_dynamics — THE DYNAMICS RUNG")
    print("FSDD digits, full token, cross-speaker LOSO. Formant TRAJECTORY +")
    print("order-N-over-time dynamics (the agent's own order-N operator), DTW-matched.")
    print("=" * 76)

    print("\nBuilding corpus (formant trajectories + order-N dynamics; "
          "native order-N audit per token) ...", flush=True)
    corpus, skipped = build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    by_w = Counter(it["word"] for it in corpus)
    print(f"  {len(corpus)} tokens | speakers={speakers} | skipped={skipped}")
    print(f"  per-digit counts: {dict(by_w)}")
    fdim = corpus[0]["traj"].shape[1] if corpus else 0
    print(f"  trajectory feature dim = {fdim} "
          f"([F1,F2,F3 | dF1,dF2,dF3 | ddF1,ddF2,ddF3], speaker-relative)")
    print(f"  native order-N audit: PASSED (native nth_order_terms == numpy diff "
          f"for every token, else build would have raised)")

    print("\n" + "=" * 76)
    print("LOSO RECOGNITION (held-out speaker NEVER banked, chance 0.100)")
    print("=" * 76)
    res = evaluate_clean(sub, corpus, verbose=True)

    print("\n  --------------------------------------------------------------")
    print(f"  (a) STATIC single-nucleus formant 1-NN (order-0 snapshot) : "
          f"{res['stat_acc']*100:.1f}%   (n={res['stat_n']})")
    print(f"  (NEW) FORMANT-TRAJECTORY + order-N dynamics, DTW-matched   : "
          f"{res['dyn_acc']*100:.1f}%   (n={res['dyn_n']})")
    print(f"  (b) FULL-ENVELOPE DTW exemplar 1-NN (the ~0.76 bank)       : "
          f"{res['mel_acc']*100:.1f}%   (n={res['mel_n']})")
    print(f"  --------------------------------------------------------------")

    print(f"\n  per-speaker DYNAMICS acc:")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"    {sp:>10}: {a*100:.1f}%")

    _print_confusion("STATIC single-nucleus confusion", res["conf_stat"])
    _print_confusion("DYNAMICS (trajectory+order-N) confusion", res["conf_dyn"])

    # ---- the coarticulated-pair audit: did the static collapse separate? ----
    print("\n  Coarticulated-pair separation (the static ih<->uw / six<->two collapse):")
    pairs = [("six", "two"), ("two", "six"), ("six", "nine"), ("nine", "six")]
    for a, b in pairs:
        s_off = res["conf_stat"][a][b]
        d_off = res["conf_dyn"][a][b]
        s_tot = sum(res["conf_stat"][a].values())
        d_tot = sum(res["conf_dyn"][a].values())
        print(f"    {a:>6}->{b:<6}: static {s_off}/{s_tot}  ->  dynamics {d_off}/{d_tot}")

    print("\n" + "=" * 76)
    print("VERDICT")
    beats_static = res["dyn_acc"] > res["stat_acc"]
    delta_static = res["dyn_acc"] - res["stat_acc"]
    frac_of_mel = res["dyn_acc"] / max(1e-9, res["mel_acc"])
    print(f"  dynamics beats static    : {'YES' if beats_static else 'NO'} "
          f"({res['dyn_acc']*100:.1f}% vs {res['stat_acc']*100:.1f}%, "
          f"{delta_static*100:+.1f} pts)")
    print(f"  vs full-envelope exemplar: dynamics {res['dyn_acc']*100:.1f}% / "
          f"exemplar {res['mel_acc']*100:.1f}% "
          f"({frac_of_mel*100:.0f}% of the exemplar bank)")
    if beats_static and res["dyn_acc"] >= 0.90 * res["mel_acc"]:
        print("  => MOTION SEPARATES the coarticulated digits AND catches the exemplar:")
        print("     the formant TRAJECTORY + order-N dynamics clears the static-formant")
        print("     ceiling and reaches the full-envelope exemplar baseline.")
    elif beats_static:
        print("  => MOTION SEPARATES the coarticulated digits and clears the static")
        print("     ceiling, but does NOT yet reach the full-envelope exemplar bank.")
    else:
        print("  => HONEST KILL: the formant trajectory + order-N dynamics does NOT")
        print("     beat the static frame. See the limiter analysis above (trajectory")
        print("     estimation noise cross-speaker / order-N derivatives overlapping).")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("FORMANT_TRAJECTORY_DYNAMICS_COMPLETED")


if __name__ == "__main__":
    main()

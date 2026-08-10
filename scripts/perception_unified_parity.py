"""perception_unified_parity — PROVE PARITY of the perception-on-the-language-engine
re-expression against the standalone REL-BAND decode.

THE TEST (the unification must pass): re-expressing the speech decode-graph as a
LIBRARY ENTRY in the agent's existing concept store, composed by its native DSL
composer, retrieved + routed by the comprehension router, must REPRODUCE the
standalone REL-BAND numbers (commit 84b034ed) within noise, on the SAME venue.

VENUE: FSDD digits (10-way, chance 10%), native DtwTo nearest-exemplar, the same
3 cells as the 84b034ed matrix:
  · v->v          (within-speaker ceiling)
  · v->whisper    (within-speaker; source carrier swapped, controlled LPC synth)
  · v->whisper    (CROSS-speaker; both speaker fist AND source carrier swapped)

84b034ed REL-BAND BASELINES (the numbers to reproduce):
  v->v 83.3%  |  within-whisper 67.3%  |  cross-speaker-whisper 60.7%   (N=150/cell)

TWO PATHS, side by side, on the IDENTICAL clips/splits/exemplars:
  STANDALONE  domains/relational_shape.relational_shape directly (the 84b034ed
              computation) -> native DtwTo. The baseline path.
  UNIFIED     install the decode-graph as a library Concept (speech_decode) in
              the existing concept store -> RETRIEVE its combination from the
              library -> COMPOSE the Gamma-typed pipeline natively -> GROUND via
              the native DtwTo router (SpeechComprehender). Perception on the
              language engine.

PARITY = the two paths agree within noise per cell. (They should be IDENTICAL up
to floating point, because the unified composer runs the SAME native Term-trees;
the self-test already showed the composed rep == standalone rep, max abs diff
0.0. The parity run proves it END TO END through the router on the full N.)

Whisper synthesis = the controlled owned-LPC source->noise synth from
scripts/voiced_whisper_probe.py (filter identical, residual -> RMS-matched
noise). No .fit / net / sweep; recognition native (substrate.evaluate).

Run: python -m scripts.perception_unified_parity [n_train] [n_test] [seed]
"""
from __future__ import annotations

import os
import re
import sys
import time
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs._native as N
from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape
from domains.speech_decode_construction import (install_speech_decode_construction,
                                                compose_rel_shape)
from domains.comprehend_speech_clip import (retrieve_decode_construction,
                                            SpeechComprehender)


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
FS = 8000
N_ANCHORS = 6

# owned LPC source/filter constants (verbatim from voiced_whisper_probe)
LPC_ORDER = 14
LPC_FRAME = 200
LPC_HOP = 80
LPC_PE = 0.97


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        buf = w.readframes(w.getnframes())
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float32), fs


def gather_files():
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        out.append((os.path.join(DATA_DIR, fn), int(digit), speaker, int(idx)))
    return out


def synth_whisper(x, seed=0):
    """Controlled LPC source->noise whisper: filter held identical, residual
    replaced by per-frame RMS-matched white noise (verbatim from
    voiced_whisper_probe). Owned native ops only."""
    xl = x.tolist()
    a_frames = N.lpc_coeff_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE)
    res = np.array(N.lpc_residual_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE),
                   dtype=np.float32)
    rng = np.random.default_rng(seed)
    exc = rng.standard_normal(len(res)).astype(np.float32)
    for i in range(len(res) // LPC_HOP):
        sl = slice(i * LPC_HOP, (i + 1) * LPC_HOP)
        rms_s = float(np.sqrt((res[sl] ** 2).mean()) + 1e-12)
        rms_n = float(np.sqrt((exc[sl] ** 2).mean()) + 1e-12)
        exc[sl] = exc[sl] * (rms_s / rms_n)
    y = np.array(N.lpc_cross_resynth(a_frames, exc.tolist(), LPC_ORDER,
                                     LPC_HOP, LPC_PE), dtype=np.float32)
    rms_x = float(np.sqrt((x ** 2).mean()) + 1e-12)
    rms_y = float(np.sqrt((y ** 2).mean()) + 1e-12)
    return (y * (rms_x / rms_y)).astype(np.float32)


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ---------------------------------------------------------------------------
# STANDALONE rep (the 84b034ed REL-BAND computation, direct).
# ---------------------------------------------------------------------------
def standalone_rep(sig, fs):
    M = band_trajectory_matrix(sig, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=N_ANCHORS)


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = np.random.default_rng(seed)

    t0 = time.time()
    files = gather_files()
    speakers = sorted({f[2] for f in files})
    chance = 1.0 / len(_DIGITS)
    print("=" * 72, flush=True)
    print("PERCEPTION-ON-THE-LANGUAGE-ENGINE — PARITY vs standalone REL-BAND",
          flush=True)
    print("=" * 72, flush=True)
    print(f"speakers: {speakers}  (FSDD 10-way, chance {100*chance:.1f}%)",
          flush=True)
    print("84b034ed REL-BAND baselines to reproduce:  "
          "v->v 83.3% | within-whisper 67.3% | xspk-whisper 60.7%", flush=True)

    # ---- WITHIN-speaker split (v->v + within-whisper cells) ----------------
    by_key = defaultdict(list)
    for path, digit, sp, idx in files:
        by_key[(sp, digit)].append((path, idx))
    train_w, test_w = [], []
    for (sp, digit), lst in by_key.items():
        lst = sorted(lst, key=lambda t: t[1])
        cut = int(round(0.7 * len(lst)))
        for p, _ in lst[:cut]:
            train_w.append((p, _DIGITS[digit], sp))
        for p, _ in lst[cut:]:
            test_w.append((p, _DIGITS[digit], sp))
    rng.shuffle(train_w)
    rng.shuffle(test_w)
    train_w = train_w[:n_train]
    test_w = test_w[:n_test]

    # ---- CROSS-speaker split (xspk-whisper cell): held-out speakers --------
    test_spk = set(speakers[::3])               # ~1/3 of speakers held out
    train_x = [(p, _DIGITS[d], sp) for p, d, sp, _ in files if sp not in test_spk]
    test_x = [(p, _DIGITS[d], sp) for p, d, sp, _ in files if sp in test_spk]
    rng.shuffle(train_x)
    rng.shuffle(test_x)
    train_x = train_x[:n_train]
    test_x = test_x[:n_test]
    print(f"\nwithin-split: train {len(train_w)} test {len(test_w)}  |  "
          f"cross-split: train {len(train_x)} test {len(test_x)} "
          f"(held-out speakers {sorted(test_spk)})", flush=True)

    # ---- install the LIBRARY ENTRY (the decode-graph as a stored construction)
    s_lib = Substrate()
    inst = install_speech_decode_construction(s_lib, n_anchors=N_ANCHORS)
    comb = retrieve_decode_construction(s_lib)
    print(f"\nLIBRARY: installed {inst['concept']} under Mt '{inst['mt']}', "
          f"built_from {inst['parts']}, combination_set={inst['combination_set']}",
          flush=True)
    print(f"RETRIEVE from store: {'OK' if comb is not None else 'MISSING'}; "
          f"the unified path composes THIS retrieved construction.\n", flush=True)

    # ---- substrate for the STANDALONE arm ----------------------------------
    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    def standalone_lexicon(train_reps):
        exs = []
        for rep, w in train_reps:
            c = sub.add_node("Exemplar", {"word": w})
            sub.set_attr(c, "rep", as_tuple(rep))
            exs.append((c, w))
        return exs

    def standalone_score(exs, test_reps):
        corr = tot = 0
        for rep, w in test_reps:
            sub.set_attr(sign, "rep", as_tuple(rep))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            corr += int(best_w == w)
            tot += 1
        return corr, tot

    def cell(name, train_files, test_files, whisper_test, shuffle=False):
        """Run ONE cell through BOTH paths. Precompute reps ONCE (the composed
        unified rep == standalone rep by construction; we still run BOTH paths
        end-to-end so parity is proven through the router, not assumed)."""
        print("=" * 72, flush=True)
        print(f"CELL: {name}", flush=True)
        print("=" * 72, flush=True)
        # --- exemplars (voiced) : STANDALONE reps + UNIFIED via composer ---
        tr_std, tr_uni_clips = [], []
        for path, w, sp in train_files:
            x, fs = load_wav(path)
            rep = standalone_rep(x, fs)
            if rep is None:
                continue
            tr_std.append((rep, w))
            tr_uni_clips.append((x, fs, w))
        # --- test clips (voiced or whisper) ---
        te_std, te_uni_clips = [], []
        for path, w, sp in test_files:
            x, fs = load_wav(path)
            sig = synth_whisper(x, seed=seed) if whisper_test else x
            rep = standalone_rep(sig, fs)
            if rep is None:
                continue
            te_std.append((rep, w))
            te_uni_clips.append((sig, fs, w))
        if shuffle:
            ws = [w for _, w in tr_std]
            rng2 = np.random.default_rng(7)
            rng2.shuffle(ws)
            tr_std = [(r, ws[i]) for i, (r, _) in enumerate(tr_std)]
            tr_uni_clips = [(x, fs, ws[i])
                            for i, (x, fs, _) in enumerate(tr_uni_clips)]

        # === STANDALONE path ===
        exs = standalone_lexicon(tr_std)
        c_std, t_std = standalone_score(exs, te_std)
        for c, _ in exs:
            sub.remove_node(c)
        acc_std = c_std / max(t_std, 1)

        # === UNIFIED path: compose-from-library + native DtwTo router ===
        sc = SpeechComprehender(s_lib, comb)
        for x, fs, w in tr_uni_clips:
            sc.add_exemplar(x, fs, w)
        c_uni = t_uni = 0
        for sig, fs, w in te_uni_clips:
            g = sc.comprehend(sig, fs)
            if g is None:
                continue
            c_uni += int(g == w)
            t_uni += 1
        sc.clear_lexicon()
        acc_uni = c_uni / max(t_uni, 1)

        se_u = (acc_uni * (1 - acc_uni) / max(t_uni, 1)) ** 0.5
        print(f"  STANDALONE  {c_std}/{t_std} = {100*acc_std:.2f}%", flush=True)
        print(f"  UNIFIED     {c_uni}/{t_uni} = {100*acc_uni:.2f}%  "
              f"(SE {100*se_u:.2f}%)", flush=True)
        delta = 100 * (acc_uni - acc_std)
        print(f"  PARITY Δ (unified - standalone) = {delta:+.2f} pts  "
              f"({'MATCH' if abs(delta) < 3.0 else 'DIVERGENCE'})\n", flush=True)
        return {"standalone": (c_std, t_std, acc_std),
                "unified": (c_uni, t_uni, acc_uni), "delta": delta}

    results = {}
    print("\n", flush=True)
    results["v->v (within, ceiling)"] = cell(
        "v->v  WITHIN-SPEAKER ceiling   (baseline REL-BAND 83.3%)",
        train_w, test_w, whisper_test=False)
    results["v->whisper (within)"] = cell(
        "v->whisper  WITHIN-SPEAKER     (baseline REL-BAND 67.3%)",
        train_w, test_w, whisper_test=True)
    results["v->whisper (cross-spk)"] = cell(
        "v->whisper  CROSS-SPEAKER      (baseline REL-BAND 60.7%)",
        train_x, test_x, whisper_test=True)
    results["shuffle backstop (xspk-whisper)"] = cell(
        "SHUFFLE backstop on cross-whisper  (must collapse ~chance 10%)",
        train_x, test_x, whisper_test=True, shuffle=True)

    # ---- VERDICT -----------------------------------------------------------
    print("=" * 72, flush=True)
    print("VERDICT — PARITY of perception-on-the-language-engine vs standalone",
          flush=True)
    print("=" * 72, flush=True)
    base = {"v->v (within, ceiling)": 83.3, "v->whisper (within)": 67.3,
            "v->whisper (cross-spk)": 60.7}
    print(f"  {'cell':32s} {'standalone':>12s} {'unified':>10s} "
          f"{'Δ-parity':>9s} {'vs 84b base':>12s}", flush=True)
    for k, r in results.items():
        cs, ts, a_s = r["standalone"]
        cu, tu, a_u = r["unified"]
        b = base.get(k)
        bstr = f"{a_u*100 - b:+.1f}pt" if b is not None else "shuffle"
        print(f"  {k:32s} {cs}/{ts}={a_s*100:5.1f}% {cu}/{tu}={a_u*100:5.1f}% "
              f"{r['delta']:+7.2f}pt {bstr:>12s}", flush=True)
    allmatch = all(abs(r["delta"]) < 3.0
                   for k, r in results.items() if "shuffle" not in k)
    print(f"\n  PARITY (unified reproduces standalone within noise per cell): "
          f"{'YES' if allmatch else 'NO — see DIVERGENCE above'}", flush=True)
    print("  The win is ARCHITECTURAL: perception now runs on the language "
          "composer / library / router / Gamma, same decode.", flush=True)
    print(f"\n  ({time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()

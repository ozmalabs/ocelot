"""audio_basis_choose — THE AGENT CHOOSES ITS OWN BASIS FOR AUDIO, then we validate.

PIPELINE (auditable, three stages)
----------------------------------
STAGE 1  GENERATE the candidate basis family (domains/audio_basis): five composed
         gammatone filterbanks spanning ANATOMICAL (LINEAR, ERB) -> STRUCTURAL
         (LOG, OCTAVE), MEL between.  ERB@32 = the existing gammatone front end.

STAGE 2  SELECT by a PRINCIPLED, LABEL-FREE criterion (domains/audio_basis_select):
           (a) SHIFT-COHERENCE  — does the SAME word across speakers differ by ~a
               pure TRANSLATION of the spectral pattern along the band axis?
               (VTL = multiplicative on Hz = additive shift in log-Hz).  Median
               best-single-shift residual ratio; LOWER = more coherent.  PRIMARY.
           (b) COMPRESSION  — effective spectral dimensionality + a quantised
               description length; LOWER = more compressible.  CORROBORATING.
         The agent PICKS the basis with the lowest shift-coherence residual.
         NO recognition labels, NO accuracy, NO sweep-to-maximise-accuracy.

STAGE 3  VALIDATE (confirmation, NOT the selector): re-represent speech in the
         CHOSEN basis and in the DEFAULT gammatone (ERB) basis, run the SAME native
         relational-rank decoder (domains/relational_shape -> native DtwTo
         nearest-exemplar) on:
            - CROSS-SPEAKER  FSDD 10-way, held-out speakers (train/test disjoint).
            - VOICED vs WHISPER  (scripts.voiced_whisper_probe.synth_whisper) within
              the same held-out test set, exemplars VOICED.
         The validation ACCURACY CONFIRMS the principled choice; it must NOT have
         been the selector.

READ THE NUMBERS: selector value per basis, the chosen basis, the validation cells
k/N + % (chosen vs gammatone) on cross-speaker and whisper.  Honest outcomes:
  (a) chosen basis more coherent AND validates -> agent picked a better basis;
  (b) chosen compresses better but recognition ~same -> coherence w/o accuracy;
  (c) gammatone already near the optimum -> anatomy was already good.

Run: python -m scripts.audio_basis_choose [n_per_spk_per_digit] [n_bands] [seed]
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

from substrate_rs import Substrate
import domains.recognition_graph as RG
from domains.audio_basis import candidate_family, band_trajectory_basis
from domains import audio_basis_select as SEL
from domains.relational_shape import relational_shape
from scripts.voiced_whisper_probe import synth_whisper


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
FS = 8000


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


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ---------------------------------------------------------------------------
# Native DtwTo nearest-exemplar over the relational-rank shape.  Identical
# machinery to scripts.relational_shape_xspeaker / voiced_whisper_probe.
# ---------------------------------------------------------------------------
def make_decoder():
    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))
    return sub, sign, err


def score(sub, sign, err, exs, test_reprs):
    corr = tot = 0
    per_word = defaultdict(lambda: [0, 0])
    for M, w in test_reprs:
        if M is None or len(M) < 2:
            continue
        sub.set_attr(sign, "rep", as_tuple(M))
        best_d, best_w = 1e18, None
        for c, ew in exs:
            d = sub.evaluate(err, {"s": sign, "w": c})
            if d < best_d:
                best_d, best_w = d, ew
        ok = int(best_w == w)
        corr += ok
        tot += 1
        per_word[w][0] += ok
        per_word[w][1] += 1
    acc = corr / max(tot, 1)
    se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
    return {"corr": corr, "tot": tot, "acc": acc, "se": se,
            "per_word": dict(per_word)}


def build_lexicon(sub, train_reprs):
    exs = []
    for M, w in train_reprs:
        if M is None or len(M) < 2:
            continue
        c = sub.add_node("Exemplar", {"word": w})
        sub.set_attr(c, "rep", as_tuple(M))
        exs.append((c, w))
    return exs


def teardown(sub, exs):
    for c, _ in exs:
        sub.remove_node(c)


# ---------------------------------------------------------------------------
def main():
    n_pspd = int(sys.argv[1]) if len(sys.argv) > 1 else 8   # clips/speaker/digit
    n_bands = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = np.random.default_rng(seed)

    t0 = time.time()
    files = gather_files()
    speakers = sorted({f[2] for f in files})
    chance = 1.0 / len(_DIGITS)

    print("=" * 74, flush=True)
    print("THE AGENT CHOOSES ITS OWN BASIS FOR AUDIO", flush=True)
    print("=" * 74, flush=True)
    print(f"FSDD speakers: {speakers}  (10-way, chance {100*chance:.1f}%)", flush=True)
    print(f"n_bands per basis: {n_bands}", flush=True)

    family = candidate_family(n_bands=n_bands)
    print("\nSTAGE 1 — candidate basis family (composed gammatone filterbanks, "
          "NOT fitted):", flush=True)
    for name, centres, bw in family:
        bwtag = "ERB-bw" if bw is None else f"constant-Q={bw}"
        print(f"  {name:7s}  {len(centres)} bands  {bwtag}  "
              f"centres {centres[0]:.0f}..{centres[-1]:.0f} Hz  "
              f"(e.g. {centres[1]:.0f},{centres[len(centres)//2]:.0f},"
              f"{centres[-2]:.0f})", flush=True)
    print("  ERB@%d = the existing gammatone front end (the BASELINE / default)."
          % n_bands, flush=True)

    # ---- cross-speaker split: hold out whole speakers --------------------------
    test_spk = set(speakers[::3])           # ~1/3 of speakers held out for test
    train_spk = [s for s in speakers if s not in test_spk]
    print(f"\nspeaker split: TRAIN {sorted(train_spk)}  |  TEST {sorted(test_spk)} "
          f"(DISJOINT)", flush=True)

    # sample a balanced clip set per (speaker,digit)
    by_key = defaultdict(list)
    for path, digit, sp, idx in files:
        by_key[(sp, digit)].append(path)
    train_clips, test_clips = [], []
    for (sp, digit), lst in by_key.items():
        lst = sorted(lst)
        pick = list(rng.choice(lst, size=min(n_pspd, len(lst)), replace=False))
        for p in pick:
            (test_clips if sp in test_spk else train_clips).append((p, digit, sp))
    rng.shuffle(train_clips)
    rng.shuffle(test_clips)
    print(f"train clips {len(train_clips)} | test clips {len(test_clips)}  "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ---- load audio once; cache signals + whisper versions ---------------------
    print("\nloading audio (+ synth-whisper of the test set)...", flush=True)
    train_sig = []
    for p, d, sp in train_clips:
        x, fs = load_wav(p)
        train_sig.append((x, fs, d, sp))
    test_sig = []
    for p, d, sp in test_clips:
        x, fs = load_wav(p)
        xw = synth_whisper(x, seed=seed)
        test_sig.append((x, xw, fs, d, sp))
    print(f"  loaded train {len(train_sig)} test {len(test_sig)} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ===========================================================================
    # STAGE 2 — the LABEL-FREE SELECTOR over the candidate bases.
    # For EACH basis: build VOICED band trajectories for the WHOLE pool (train+test
    # speakers — the selector is unsupervised, it may see all speakers; it never
    # sees the recognition decision), then compute shift-coherence + compression.
    # ===========================================================================
    print("\n" + "=" * 74, flush=True)
    print("STAGE 2 — PRINCIPLED LABEL-FREE SELECTOR (compression / shift-coherence)",
          flush=True)
    print("=" * 74, flush=True)
    print("  PRIMARY: shift-coherence residual ratio (VTL=shift; LOWER=more coherent)",
          flush=True)
    print("  CORROBORATING: effective spectral dim + DL bits/band (LOWER=more "
          "compressible)", flush=True)
    print("  NOTE: word identity groups same-word pairs ONLY; NO accuracy, NO "
          "decoder here.\n", flush=True)

    # all VOICED signals pooled, tagged by digit (for grouping) and speaker
    pool = ([(x, d) for (x, fs, d, sp) in train_sig] +
            [(x, d) for (x, xw, fs, d, sp) in test_sig])

    per_basis = {}
    for name, centres, bw in family:
        # cross-speaker, same-word grouping for shift-coherence
        mats_by_word = defaultdict(list)
        all_mats = []
        for x, d in pool:
            M = band_trajectory_basis(x, FS, centres, n_frames=n_bands, bw_mode=bw)
            mats_by_word[_DIGITS[d]].append(M)
            all_mats.append(M)
        sr, sn = SEL.shift_coherence(mats_by_word, rng=rng)
        edim, dlb, cn = SEL.compression(all_mats)
        per_basis[name] = {"shift_ratio": sr, "shift_n": sn,
                           "eff_dim": edim, "dl_bits": dlb, "comp_n": cn}
        flag = "  <- DEFAULT GAMMATONE" if name == "ERB" else ""
        print(f"  {name:7s}  shift-coherence resid-ratio = {sr:.4f} (n={sn})   "
              f"eff-dim = {edim:5.2f}   DL = {dlb:6.1f} bits/band{flag}", flush=True)

    chosen, ranked = SEL.select(per_basis)
    print("\n  RANKING by shift-coherence (PRIMARY, ascending = more coherent):",
          flush=True)
    for nm, sr, ed, dl in ranked:
        mark = " <== CHOSEN" if nm == chosen else ""
        print(f"    {nm:7s}  shift-ratio {sr:.4f}   eff-dim {ed:5.2f}   "
              f"DL {dl:6.1f}{mark}", flush=True)
    print(f"\n  >>> THE AGENT CHOOSES: {chosen}  "
          f"(lowest shift-coherence residual = the same word differs by ~a SHIFT;\n"
          f"      the invariance is a SIMPLE operation in this basis). "
          f"Selector NOT accuracy.", flush=True)

    # ===========================================================================
    # STAGE 3 — VALIDATION (confirmation): chosen basis vs DEFAULT gammatone (ERB),
    # SAME native relational-rank DtwTo decoder, cross-speaker + voiced/whisper.
    # ===========================================================================
    print("\n" + "=" * 74, flush=True)
    print("STAGE 3 — VALIDATION (CONFIRMATION ONLY): chosen vs gammatone (ERB)",
          flush=True)
    print("=" * 74, flush=True)
    print("  SAME native DtwTo decoder in both bases.  Accuracy CONFIRMS the "
          "principled\n  choice; it was NOT the selector.", flush=True)
    print("  Two lenses: RELATIONAL (ordinal band-rank, the current REL-BAND decoder "
          "— note\n  it is by-construction WARP-invariant so it is the conservative "
          "lens) and SURFACE\n  (absolute band trajectory — basis-SENSITIVE, where a "
          "better basis can show its\n  cross-speaker effect).\n", flush=True)

    spec_by_name = {nm: (centres, bw) for nm, centres, bw in family}
    erb_c, erb_bw = spec_by_name["ERB"]
    bases_to_validate = [("GAMMATONE(ERB)", erb_c, erb_bw)]
    if chosen != "ERB":
        ch_c, ch_bw = spec_by_name[chosen]
        bases_to_validate.append((f"CHOSEN({chosen})", ch_c, ch_bw))
    else:
        print("  (the agent CHOSE the gammatone/ERB basis itself — anatomy was "
              "already near the\n   coherence optimum.  Validating it as the single "
              "arm; report case (c).)\n", flush=True)

    sub, sign, err = make_decoder()
    results = {}
    for bname, centres, bw in bases_to_validate:
        print("-" * 74, flush=True)
        print(f"BASIS {bname}", flush=True)
        print("-" * 74, flush=True)
        # band trajectories once; both lenses derive from them
        tr_band = [(band_trajectory_basis(x, FS, centres, n_frames=n_bands,
                                          bw_mode=bw), _DIGITS[d])
                   for x, fs, d, sp in train_sig]
        te_band = {"voiced": [], "whisper": []}
        for x, xw, fs, d, sp in test_sig:
            te_band["voiced"].append((band_trajectory_basis(
                x, FS, centres, n_frames=n_bands, bw_mode=bw), _DIGITS[d]))
            te_band["whisper"].append((band_trajectory_basis(
                xw, FS, centres, n_frames=n_bands, bw_mode=bw), _DIGITS[d]))

        results[bname] = {}
        for lens in ("RELATIONAL", "SURFACE"):
            if lens == "RELATIONAL":
                tr_reprs = [(relational_shape(M), w) for M, w in tr_band]
                te_reprs = {c: [(relational_shape(M), w) for M, w in te_band[c]]
                            for c in ("voiced", "whisper")}
            else:
                tr_reprs = tr_band
                te_reprs = te_band
            exs = build_lexicon(sub, tr_reprs)
            rv = score(sub, sign, err, exs, te_reprs["voiced"])
            rw = score(sub, sign, err, exs, te_reprs["whisper"])
            teardown(sub, exs)
            results[bname][lens] = {"voiced": rv, "whisper": rw}
            drop = 100 * (rv['acc'] - rw['acc'])
            print(f"  [{lens:10s}] x-spk VOICED {rv['corr']}/{rv['tot']}="
                  f"{100*rv['acc']:.1f}% (SE {100*rv['se']:.1f}%)  "
                  f"WHISPER {rw['corr']}/{rw['tot']}={100*rw['acc']:.1f}% "
                  f"(SE {100*rw['se']:.1f}%)  DROP {drop:+.1f}pts  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # ---- VERDICT --------------------------------------------------------------
    print("\n" + "=" * 74, flush=True)
    print("VERDICT — selector value drove the choice; accuracy CONFIRMS", flush=True)
    print("=" * 74, flush=True)
    print(f"  chosen basis (by label-free selector): {chosen}", flush=True)
    print(f"  selector (shift-coherence resid-ratio): chosen "
          f"{per_basis[chosen]['shift_ratio']:.4f}  vs  ERB/gammatone "
          f"{per_basis['ERB']['shift_ratio']:.4f}", flush=True)
    print(f"  compression (eff-dim): chosen {per_basis[chosen]['eff_dim']:.2f}  "
          f"vs ERB {per_basis['ERB']['eff_dim']:.2f}", flush=True)
    if "GAMMATONE(ERB)" in results and chosen != "ERB":
        g = results["GAMMATONE(ERB)"]
        c = results[f"CHOSEN({chosen})"]
        print("\n  VALIDATION (cross-speaker FSDD 10-way, native DtwTo NN):",
              flush=True)
        for lens in ("RELATIONAL", "SURFACE"):
            for cond in ("voiced", "whisper"):
                ga, ca = g[lens][cond]['acc'], c[lens][cond]['acc']
                print(f"    {lens:10s} {cond:8s}: gammatone {100*ga:.1f}%  ->  "
                      f"chosen {100*ca:.1f}%  (d {100*(ca-ga):+.1f} pts)", flush=True)
        print("\n  READ THE NUMBERS: if the chosen basis's lower shift-coherence "
              "residual ALSO\n  lifts cross-speaker / whisper recognition, the agent "
              "picked a better basis than\n  anatomy gave it. If recognition is ~same "
              "while coherence improved, coherence\n  was gained without accuracy "
              "(report honestly). NEITHER was an accuracy sweep.", flush=True)
    else:
        print("\n  The agent chose the gammatone/ERB basis itself: the anatomical "
              "basis was already\n  near the coherence optimum (case c). No "
              "better-than-anatomy basis among the\n  candidates by the label-free "
              "selector.", flush=True)

    print(f"\n  total wall: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

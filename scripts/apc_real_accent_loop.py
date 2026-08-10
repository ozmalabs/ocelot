"""LANGUAGE -> PERCEPTION LOOP on a REAL ACCENTED CORPUS (Speech Accent Archive, accent.gmu.edu).

The synthetic-on-real-cochleagram loop (commit 830577f0, apc_language_perception_loop.py) proved
the mechanism: a TEXT-recovered accent transform, quotiented out of a REAL LibriSpeech cochleagram
that had a SYNTHETIC accent injected on top, recovers the canonical word-shape — and decisively
beats a random-direction control. The one missing piece was a REAL accented corpus (no synthetic
injection at all). This script closes that gap.

CORPUS: the Speech Accent Archive (accent.gmu.edu, public, cited academic corpus). Every speaker —
regardless of native language — reads the SAME FIXED elicitation paragraph ("Please call
Stella..."), so the SAME WORD is directly comparable across a native-English-US reference group
and five L1-accent groups (spanish, mandarin, russian, arabic, korean). 38 speakers total (8
reference + 6 per accent group). See scripts/saa_corpus_extract.py for the download+force-align+
cochleagram extraction (isolated MMS_FA subprocess, bootstrap/eval-only; donkey=0 in THIS process).

THE LOOP (identical machinery to apc_language_perception_loop.py, reused not reimplemented):
  text (documented L2-English phonology, eye-dialect pairs on words IN the Stella paragraph)
    --[voicing-aware g2p + Peterson-Barney formants + VecSub]-->  shift-vector in FORMANT space
    --[apc_formant_bands]-->                                       shift-vector in COCHLEAGRAM-BAND space
    --[prototype-gated SUBTRACT on the REAL accented speaker's cochleagram]--> the acoustic QUOTIENT
    --[held DtwTo + apc_recall]-->                                 does quotiented vs canonical SNAP?

Unlike the prior script, there is NO synthetic accent injection here — `acc` IS the real recording.
`textq` = the REAL accented cochleagram with the text-recovered TARGET-gated subtract applied
(scripts.apc_language_perception_loop._apply_dir, gate='tgt', reused unmodified). `randq` = the
same magnitude subtracted in a random direction (discriminative control, same helper, gate='rand').

GENERALISATION over the prior script: apc_language_perception_loop.band_shifts() only rendered
kind in (vowel_shift, th_stopping, th_fronting) into band-space (the only kinds the three
constructed accents produced). Real L1-accent phonology needs more substitution KINDS (consonant
labial mergers, TH-sibilant realisation, final-obstruent devoicing, liquid neutralisation) — all
still single-phoneme substitutions with concrete formant coordinates, so `band_shifts_general`
below drops the kind whitelist and renders ANY (src,tgt) pair with formants in PHONEME_FORMANTS.
`ext_classify` (monkeypatched onto TT.classify for THIS process only) adds those kind labels for
the linguistic-correctness bookkeeping; it does not touch the shared jabberwock_text_to_transform_
prior.py file or its three existing constructed accents.

donkey=0 in this process (no torch/torchaudio/allosaurus/whisper) — MMS_FA force-alignment ran in
an ISOLATED subprocess when the cache was built (saa_corpus_extract.py --extract).

Run:
  PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
      scripts/apc_real_accent_loop.py
"""
from __future__ import annotations
import os, sys, pickle, resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

import numpy as np
from collections import defaultdict

import substrate_rs as srs
from substrate_rs import _native as nat, Lit, Term
import scripts.jabberwock_text_to_transform_prior as TT
import scripts.apc_language_perception_loop as APL   # reused: resample, utt_feats, snap, recall, _apply_dir, _traj

SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
CACHE = os.path.join(SCRATCH, "saa_corpus_uttframes.pkl")
LIBRI_CACHE = os.path.join(SCRATCH, "apc_libri_uttframes.pkl")

T = int(os.environ.get("T", "14"))
SIGMA = float(os.environ.get("SIGMA", "0.35"))
PAIR_CAP = int(os.environ.get("PAIR_CAP", "400"))
REF_GROUP = "english_us"
ACCENT_GROUPS = ["spanish", "mandarin", "russian", "arabic", "korean"]

# APC transfer (bonus; trained on LibriSpeech, applied to SAA cochleagrams — a domain-transfer test)
RUN_APC_TRANSFER = os.environ.get("APC_TRANSFER", "1") == "1"
DH = int(os.environ.get("DH", "64")); KAHEAD = int(os.environ.get("KAHEAD", "3"))
EPOCHS = int(os.environ.get("EPOCHS", "10")); LR = float(os.environ.get("LR", "0.05"))
UTTS_TR = int(os.environ.get("UTTS_TR", "120"))


def _peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


# ============================================================================================== #
#  REAL L1-ACCENT TEXT PRIORS — documented L2-English contrastive phonology, eye-dialect pairs
#  restricted to words that ACTUALLY APPEAR in the Stella elicitation paragraph (so every
#  recovered rule is directly testable on the real corpus). Every pair was checked against the
#  agent's own sublexical g2p route (central_routes.sublexical_g2p) to confirm it produces the
#  intended phoneme substitution (see commit note); this is standard contrastive-analysis L2
#  phonology (Spanish/Mandarin/Russian/Arabic/Korean-accented English), not invented.
# ============================================================================================== #
SAA_ACCENTS = {
    "spanish": {
        "description": ("Spanish-accented English: TH-STOPPING (Spanish has no dental fricatives; "
                        "/theta/,/edh/ -> dental stops [t]/[d]: the->de, thick->tick, three->tree, "
                        "brother->broder). B/V MERGER (Spanish /b/ and /v/ are allophones of one "
                        "phoneme; /v/ realised as [b]: five->fibe). [Also documented but NOT "
                        "text-recoverable by this substitution scheme: epenthetic /e/ before "
                        "word-initial /s/+consonant clusters, e.g. store->estore — an INSERTION, "
                        "which the alignment step (Needleman-Wunsch, skips insertions) cannot turn "
                        "into a formant-space direction; honestly excluded, not fabricated.]"),
        "pairs": [("the", "de"), ("these", "dese"), ("thick", "tick"), ("three", "tree"),
                  ("brother", "broder"), ("things", "tings"), ("with", "wit"), ("five", "fibe")],
        "expected": {"th_stopping", "labial_shift"},
    },
    "mandarin": {
        "description": ("Mandarin-accented English: TH-SIBILANT realisation (Mandarin has no dental "
                        "fricatives; /theta/ -> [s], /edh/ -> [z]: things->sings, thick->sick, "
                        "three->sree, the->ze, brother->brozer). V/W confusion (Mandarin's /v/ is "
                        "not phonemic; realised close to [w]: five->fiwe)."),
        "pairs": [("things", "sings"), ("thick", "sick"), ("three", "sree"), ("the", "ze"),
                  ("brother", "brozer"), ("five", "fiwe")],
        "expected": {"th_sibilant", "labial_shift"},
    },
    "russian": {
        "description": ("Russian-accented English: TH-STOPPING (/theta/,/edh/ -> [t]/[d]: thick->"
                        "tick, three->tree, the->de, these->dese). FINAL-OBSTRUENT DEVOICING "
                        "(Russian neutralises voiced obstruents word-finally: five->fife). W/V "
                        "confusion (Russian has no /w/, uses /v/: we->ve, will->vill, wednesday->"
                        "vednesday)."),
        "pairs": [("thick", "tick"), ("three", "tree"), ("the", "de"), ("these", "dese"),
                  ("five", "fife"), ("we", "ve"), ("will", "vill"), ("wednesday", "vednesday")],
        "expected": {"th_stopping", "final_devoicing", "labial_shift"},
    },
    "arabic": {
        "description": ("Arabic-accented English: P/B MERGER (Standard Arabic has no phonemic /p/; "
                        "realised as [b]: please->blease, spoons->sboons, plastic->blastic). "
                        "FINAL-OBSTRUENT DEVOICING of /v/ (five->fife). [Arabic HAS interdental "
                        "fricatives /theta/,/edh/ so TH-stopping is NOT included here — the "
                        "documented phonology does not predict it, and including it would be "
                        "linguistically dishonest.]"),
        "pairs": [("please", "blease"), ("spoons", "sboons"), ("plastic", "blastic"),
                  ("five", "fife")],
        "expected": {"labial_shift", "final_devoicing"},
    },
    "korean": {
        "description": ("Korean-accented English: F/P substitution (Korean has no /f/; realised "
                        "close to [p]: fresh->presh, for->por, from->prom). LIQUID NEUTRALISATION "
                        "(Korean has one liquid phoneme, realised [l] in coda/onset-cluster "
                        "position where English distinguishes /r/ from /l/: red->led, bring->bling, "
                        "brother->blother)."),
        "pairs": [("fresh", "presh"), ("for", "por"), ("from", "prom"),
                  ("red", "led"), ("bring", "bling"), ("brother", "blother")],
        "expected": {"labial_shift", "liquid_neutralization"},
    },
}

_VOICED_VOICELESS_PAIRS = {("v", "f"), ("b", "p"), ("d", "t"), ("g", "k"), ("z", "s")}
_LABIAL_PAIRS = {("v", "b"), ("p", "b"), ("f", "p"), ("v", "w"), ("w", "v")}
_LIQUID_PAIRS = {("r", "l"), ("l", "r")}


def ext_classify(src, tgt):
    """Extends TT.classify with the additional substitution kinds real L1-accent phonology needs
    (TH-sibilant, final-obstruent devoicing, labial merger, liquid neutralisation). Falls back to
    the original classify() for everything it already recognises (th_stopping/th_fronting/
    g_dropping/vowel_shift/elision). Monkeypatched onto TT.classify for THIS process only — does
    not modify jabberwock_text_to_transform_prior.py or its three existing constructed accents."""
    base = _orig_classify(src, tgt)
    if base != "other":
        return base
    if tgt is None:
        return base
    if src in ("T", "D") and tgt in ("s", "z"):
        return "th_sibilant"
    if (src, tgt) in _VOICED_VOICELESS_PAIRS:
        return "final_devoicing"
    if (src, tgt) in _LABIAL_PAIRS:
        return "labial_shift"
    if (src, tgt) in _LIQUID_PAIRS:
        return "liquid_neutralization"
    return base


_orig_classify = TT.classify
TT.classify = ext_classify


# ============================================================================================== #
#  band_shifts_general — like APL.band_shifts but WITHOUT the kind whitelist (any substitution
#  with both phonemes in PHONEME_FORMANTS renders into a band-space direction; deletions cannot,
#  honestly skipped).
# ============================================================================================== #
def band_shifts_general(recovered):
    shifts = []
    for r in recovered:
        src, tgt = r["src"], r["tgt"]
        if tgt is None or src not in TT.PHONEME_FORMANTS or tgt not in TT.PHONEME_FORMANTS:
            continue
        fs = TT.PHONEME_FORMANTS[src]; ft = TT.PHONEME_FORMANTS[tgt]
        bs = np.asarray(nat.apc_formant_bands(float(fs[0]), float(fs[1]), float(fs[2]), SIGMA), np.float32)
        bt = np.asarray(nat.apc_formant_bands(float(ft[0]), float(ft[1]), float(ft[2]), SIGMA), np.float32)
        bs = bs / (bs.sum() + 1e-9); bt = bt / (bt.sum() + 1e-9)
        shifts.append({"src": src, "tgt": tgt, "kind": r["kind"], "src_shape": bs, "tgt_shape": bt,
                       "dshape": (bt - bs).astype(np.float32)})
    return shifts


def gate_hit_rate(coch, shifts, gate):
    """Diagnostic: fraction of frames whose spectral SHAPE falls within APL.RADIUS of some rule
    prototype (i.e. actually gets quotiented). Honesty check on whether the synthetic-tuned
    prototype-gate radius transfers to real, noisier accented recordings."""
    coch = np.asarray(coch, np.float32); E = coch.sum(1, keepdims=True) + 1e-9; shape = coch / E
    hits = 0
    for i in range(coch.shape[0]):
        bd = min((float(np.sum((shape[i] - (r["src_shape"] if gate == "src" else r["tgt_shape"])) ** 2)))
                 for r in shifts)
        if bd < APL.RADIUS:
            hits += 1
    return hits / max(1, coch.shape[0])


def gate_discrimination(coch, wspans, undergoes, shifts):
    """Diagnostic: does the prototype-shape gate distance actually separate frames INSIDE an
    accent-bearing word span from frames elsewhere in the same utterance? On the synthetic
    single-word renders this distinction was moot (nothing else in the buffer); on a REAL full
    sentence it is the crux of whether the blind full-utterance quotient is WORD-TARGETED or
    diffuse/indiscriminate. Returns (median target-frame dist, median non-target-frame dist)."""
    coch = np.asarray(coch, np.float32); E = coch.sum(1, keepdims=True) + 1e-9; shape = coch / E
    target = set()
    for (w, f0, f1) in wspans:
        if undergoes(w):
            target.update(range(f0, f1))
    dists = np.array([min(float(np.sum((shape[i] - r["tgt_shape"]) ** 2)) for r in shifts)
                      for i in range(coch.shape[0])])
    tgt_idx = sorted(target); non_idx = [i for i in range(coch.shape[0]) if i not in target]
    return (float(np.median(dists[tgt_idx])) if tgt_idx else float("nan"),
            float(np.median(dists[non_idx])) if non_idx else float("nan"))


# ============================================================================================== #
#  STEP-2 FIXES for the real-accent gate (the 2/5 convergence fix):
#    (b) PER-SPEAKER CHANNEL QUOTIENT — subtract each speaker's OWN mean frame FIRST, stripping the
#        dominant additive channel/level/rate component (documented as 55-65% of the raw cross-
#        speaker gap). Unsupervised, generalises to unseen speakers. Applied IDENTICALLY to the
#        canonical reference and to every accented condition, in BOTH band and APC-rep space.
#    (a) LOCUS-GATED text transform + APC-REP gate — instead of the blind prototype-shape RADIUS
#        gate that fired on 77-93% of frames across the whole sentence, KEEP the text-recovered
#        subtract only WITHIN accent-bearing word spans (text-identified via undergoes()), and
#        measure recovery in the APC LEARNED REPRESENTATION (sharper than the raw 32-band
#        cochleagram) so the accent phonetic locus is localised, not diffuse.
# ============================================================================================== #
SPK_QUOT = os.environ.get("SPK_QUOT", "1") == "1"
LOCUS_GATE = os.environ.get("LOCUS_GATE", "1") == "1"


def spk_quot_utt(x):
    """Per-speaker (= per-utterance in SAA, one paragraph per speaker) CHANNEL QUOTIENT: subtract
    the speaker's own mean frame. Strips the dominant additive channel/level component. Works on
    a cochleagram OR an APC-rep trajectory (any [T, D] array)."""
    x = np.asarray(x, np.float32)
    return x - x.mean(0, keepdims=True)


def apply_dir_locus(coch, shifts, gate, wspans, undergoes_fn, rng=None):
    """The text-recovered transform APPLIED AT ITS LOCUS. Runs APL._apply_dir (prototype-gated
    per-frame subtract) but KEEPS the change only within accent-bearing WORD spans (identified from
    TEXT via undergoes_fn); frames elsewhere are left untouched. This localises the quotient to the
    accent phonetic locus instead of the blind whole-sentence RADIUS gate (which fired on 77-93% of
    frames). When LOCUS_GATE is off, falls back to the original whole-utterance behaviour."""
    out = APL._apply_dir(coch, shifts, gate, rng)
    if not LOCUS_GATE:
        return out
    coch = np.asarray(coch, np.float32)
    mask = np.zeros(coch.shape[0], bool)
    for (w, f0, f1) in wspans:
        if undergoes_fn(w):
            mask[f0:f1] = True
    res = coch.copy()
    res[mask] = out[mask]
    return res


def main():
    resource.setrlimit(resource.RLIMIT_AS, (10 * 1024 ** 3, 10 * 1024 ** 3))
    if not os.path.exists(CACHE):
        print(f"BLOCKED: no SAA corpus cache at {CACHE} — run scripts/saa_corpus_extract.py --extract "
              f"first (isolated MMS_FA bootstrap).")
        return
    print(f"  [substrate_rs] {nat.__file__}", flush=True)
    assert hasattr(nat, "apc_formant_bands"), "apc_formant_bands missing — rebuild the crate"

    data = pickle.load(open(CACHE, "rb"))
    by_group = defaultdict(list)
    for (coch, wspans, spk, grp) in data:
        by_group[grp].append((coch, wspans, spk))
    ref = by_group[REF_GROUP]
    n_spk_total = len(data)
    print(f"\n== LANGUAGE->PERCEPTION LOOP on the REAL Speech Accent Archive corpus ==")
    print(f"  {n_spk_total} speakers | reference '{REF_GROUP}': {len(ref)} spk | "
          f"accent groups: " + ", ".join(f"{g}={len(by_group[g])}" for g in ACCENT_GROUPS))

    # canonical (reference) word -> list of (coch_slice) across ALL reference speakers.
    # ref_word_slices    = raw band slices (original gate); ref_word_slices_q = per-speaker
    # channel-quotiented band slices (STEP-2 fix b).
    ref_word_slices = defaultdict(list)
    ref_word_slices_q = defaultdict(list)
    for (coch, wspans, spk) in ref:
        coch = np.asarray(coch, np.float32)
        cq = spk_quot_utt(coch)
        for (w, f0, f1) in wspans:
            ref_word_slices[w].append(APL.resample(coch[f0:f1], T))
            ref_word_slices_q[w].append(APL.resample(cq[f0:f1], T))

    s = srs.Substrate()
    pnode = TT.seed_phoneme_formants(s); TT.seed_voicing_lexicon(s)

    # ---------- optional: APC transfer front-end (trained on LibriSpeech, applied here) ----------
    apc_model = None; mu_a = sd_a = None
    if RUN_APC_TRANSFER and os.path.exists(LIBRI_CACHE):
        libri = pickle.load(open(LIBRI_CACHE, "rb"))
        tr = [d for d in libri if d[3] == "train"][:UTTS_TR]
        tr_feats = [APL.utt_feats(np.asarray(d[0], np.float32)) for d in tr]
        stk = np.concatenate(tr_feats); mu_a, sd_a = stk.mean(0), stk.std(0) + 1e-6
        tr_feats = [((f - mu_a) / sd_a).astype(np.float32) for f in tr_feats]
        ff = np.concatenate([f.reshape(-1) for f in tr_feats]).astype(np.float32)
        lens = [int(f.shape[0]) for f in tr_feats]
        din = tr_feats[0].shape[1]
        print(f"\n  [APC transfer] training APC on {len(tr)} LibriSpeech utts (din={din} dh={DH} "
              f"K={KAHEAD} epochs={EPOCHS}) -- applied to SAA cochleagrams (domain-transfer, "
              f"honestly reported as a bonus, NOT the primary gate) ...", flush=True)
        apc_model = [float(v) for v in nat.apc_train(ff.tolist(), lens, din, DH, KAHEAD, EPOCHS, LR,
                                                      False, 0, False)]
    ns = nat.Substrate()
    def apc_encode(featseq):
        term = {"type": "ApcEncode", "model": {"type": "Lit", "value": apc_model},
                "seq": {"type": "Lit", "value": APL._traj(featseq)},
                "start": {"type": "Lit", "value": -1}, "end": {"type": "Lit", "value": -1},
                "out_len": {"type": "Lit", "value": int(featseq.shape[0])}}
        return np.asarray([[float(v) for v in row] for row in ns.evaluate(term, {})], np.float32)

    ref_word_apc = defaultdict(list)      # raw APC-rep slices
    ref_word_apc_q = defaultdict(list)    # per-speaker-quotiented APC-rep slices (STEP-2 fix b)
    if apc_model is not None:
        for (coch, wspans, spk) in ref:
            coch = np.asarray(coch, np.float32)
            f = APL.utt_feats(coch); f = ((f - mu_a) / sd_a).astype(np.float32)
            h = apc_encode(f); hq = spk_quot_utt(h)
            for (w, f0, f1) in wspans:
                ref_word_apc[w].append(APL.resample(h[f0:f1], T))
                ref_word_apc_q[w].append(APL.resample(hq[f0:f1], T))

    all_summ = []
    for grp in ACCENT_GROUPS:
        spec = SAA_ACCENTS[grp]
        at, recovered = TT.recover(s, pnode, grp, spec)
        feats = {r["kind"] for r in recovered if r["kind"] != "other"}
        exp = spec["expected"]
        ling_ok = exp.issubset(feats)
        shifts = band_shifts_general(recovered)
        print(f"\n{'='*100}\nACCENT GROUP: {grp}  ({len(by_group[grp])} real speakers, "
              f"native language self-reported '{grp}')")
        print(f"  --- recovered phoneme transform (from TEXT only; documented L2-English phonology) ---")
        for r in recovered:
            tgt = r["tgt"] if r["tgt"] is not None else "(elided)"
            print(f"      {r['src']:>3} -> {tgt:<8} [{r['kind']:<20}] x{r['support']}  ({', '.join(r['ex'])})")
        print(f"  linguistic correctness: expected {sorted(exp)} vs recovered {sorted(feats)} -> "
              f"{'MATCH' if ling_ok else 'MISMATCH'}")
        print(f"  {len(shifts)} shift-vector(s) rendered into COCHLEAGRAM-BAND space")

        src_ph = {r["src"] for r in shifts}
        if not src_ph:
            print(f"  NO renderable shift-vectors for this accent — SKIPPING (honest: nothing to quotient)")
            continue

        def undergoes(w):
            return any(p in src_ph for p in TT.g2p_voiced(w))

        # ---------- per-accent-speaker: build word-matched canon/acc/textq/randq slices ----------
        # band  = raw cochleagram band slices (ORIGINAL gate; textq now LOCUS-gated when LOCUS_GATE)
        # bandq = per-speaker channel-quotiented band slices  (STEP-2 fix b, band space)
        # apcS  = raw APC-rep slices                           (APC space, locus transform)
        # apcq  = per-speaker-quotiented APC-rep slices        (STEP-2 PRIMARY GATE: fix a + fix b)
        rng = np.random.default_rng(hash(grp) % (2**31))
        words, spk_ids = [], []
        band = {"canon": [], "acc": [], "textq": [], "randq": []}
        bandq = {"canon": [], "acc": [], "textq": [], "randq": []}
        apcS = {"canon": [], "acc": [], "textq": [], "randq": []}
        apcq = {"canon": [], "acc": [], "textq": [], "randq": []}
        hit_blind, nfr_tot, locus_mod = 0.0, 0, 0
        disc_tgt, disc_non = [], []
        for (coch, wspans, spk) in by_group[grp]:
            coch = np.asarray(coch, np.float32)
            wspans_u = [(w, f0, f1) for (w, f0, f1) in wspans if undergoes(w) and w in ref_word_slices]
            if not wspans_u:
                continue
            # LOCUS-gated text transform (fix a): keep the subtract only inside accent-bearing words
            textq_utt = apply_dir_locus(coch, shifts, "tgt", wspans, undergoes)
            randq_utt = apply_dir_locus(coch, shifts, "rand", wspans, undergoes, rng)
            # gate diagnostics: BLIND whole-sentence RADIUS-hit (the 77-93%) vs LOCUS-restricted frames
            hit_blind += gate_hit_rate(coch, shifts, "tgt") * coch.shape[0]
            nfr_tot += coch.shape[0]
            locus_mod += int(np.any(np.abs(textq_utt - coch) > 1e-6, axis=1).sum())
            dt, dn = gate_discrimination(coch, wspans, undergoes, shifts)
            disc_tgt.append(dt); disc_non.append(dn)
            cq = spk_quot_utt(coch); tq_q = spk_quot_utt(textq_utt); rq_q = spk_quot_utt(randq_utt)
            if apc_model is not None:
                f_raw = APL.utt_feats(coch); f_raw = ((f_raw - mu_a) / sd_a).astype(np.float32)
                f_tq = APL.utt_feats(textq_utt); f_tq = ((f_tq - mu_a) / sd_a).astype(np.float32)
                f_rq = APL.utt_feats(randq_utt); f_rq = ((f_rq - mu_a) / sd_a).astype(np.float32)
                h_raw = apc_encode(f_raw); h_tq = apc_encode(f_tq); h_rq = apc_encode(f_rq)
                h_raw_q = spk_quot_utt(h_raw); h_tq_q = spk_quot_utt(h_tq); h_rq_q = spk_quot_utt(h_rq)
            for (w, f0, f1) in wspans_u:
                # pick ONE reference canonical token per word (rotate across ref speakers deterministically)
                ci = hash((w, spk)) % len(ref_word_slices[w])
                words.append(w); spk_ids.append(spk)
                band["canon"].append(ref_word_slices[w][ci])
                band["acc"].append(APL.resample(coch[f0:f1], T))
                band["textq"].append(APL.resample(textq_utt[f0:f1], T))
                band["randq"].append(APL.resample(randq_utt[f0:f1], T))
                bandq["canon"].append(ref_word_slices_q[w][ci])
                bandq["acc"].append(APL.resample(cq[f0:f1], T))
                bandq["textq"].append(APL.resample(tq_q[f0:f1], T))
                bandq["randq"].append(APL.resample(rq_q[f0:f1], T))
                if apc_model is not None and w in ref_word_apc:
                    ci2 = hash((w, spk, "a")) % max(1, len(ref_word_apc.get(w, [])) or 1)
                    apcS["canon"].append(ref_word_apc[w][ci2])
                    apcS["acc"].append(APL.resample(h_raw[f0:f1], T))
                    apcS["textq"].append(APL.resample(h_tq[f0:f1], T))
                    apcS["randq"].append(APL.resample(h_rq[f0:f1], T))
                    apcq["canon"].append(ref_word_apc_q[w][ci2])
                    apcq["acc"].append(APL.resample(h_raw_q[f0:f1], T))
                    apcq["textq"].append(APL.resample(h_tq_q[f0:f1], T))
                    apcq["randq"].append(APL.resample(h_rq_q[f0:f1], T))
        for c in band:
            band[c] = np.asarray(band[c], np.float32); bandq[c] = np.asarray(bandq[c], np.float32)
        nw = len(set(words))
        blind_pct = 100.0 * hit_blind / max(1, nfr_tot)
        locus_pct = 100.0 * locus_mod / max(1, nfr_tot)
        med_tgt = float(np.nanmedian(disc_tgt)) if disc_tgt else float("nan")
        med_non = float(np.nanmedian(disc_non)) if disc_non else float("nan")
        print(f"  {len(words)} accent-bearing word tokens ({nw} distinct words, "
              f"{len(set(spk_ids))} real accented speakers)")
        print(f"  ★ GATE-DISCRIMINATION (fix a): BLIND whole-sentence RADIUS gate fired on "
              f"{blind_pct:.1f}% of frames; LOCUS-gated transform now modifies only {locus_pct:.1f}% "
              f"(accent-bearing word frames within radius) — {'SELECTIVE' if locus_pct < blind_pct * 0.5 else 'still broad'}")
        print(f"  DIAGNOSTIC (word-targeting): median prototype-shape distance WITHIN accent-bearing "
              f"words {med_tgt:.4f} vs ELSEWHERE {med_non:.4f}  "
              f"({'WORD-TARGETED' if med_tgt < med_non * 0.8 else 'INDISCRIMINATE (raw-band gate)'})")
        gate_pct = blind_pct
        if len(words) < 6:
            print(f"  TOO FEW word tokens for a stable metric on this group — honest fork: SKIPPING "
                  f"({len(words)} < 6). Likely cause: too few src-phoneme words survived alignment "
                  f"quality filters, not a modelling failure.")
            continue

        def snap4(D, wds, sids):
            fl = APL.snap(s, D["canon"], D["canon"], wds, sids, PAIR_CAP)
            rw = APL.snap(s, D["canon"], D["acc"], wds, sids, PAIR_CAP)
            tx = APL.snap(s, D["canon"], D["textq"], wds, sids, PAIR_CAP)
            rn = APL.snap(s, D["canon"], D["randq"], wds, sids, PAIR_CAP)
            ok = tx < rw - 1e-3 and tx < rn - 1e-3
            fr = (rw - tx) / max(rw - fl, 1e-9)
            return fl, rw, tx, rn, ok, fr

        floor, raw, txt, rnd, snap_ok, frac = snap4(band, words, spk_ids)
        print(f"  --- SNAP on RAW cochleagram-BAND space (original gate; locus transform) ---")
        print(f"      floor {floor:.4f} | raw {raw:.4f} | +text {txt:.4f} ({frac*100:.0f}% removed) | "
              f"+rand {rnd:.4f}  => {'SNAP' if snap_ok else 'NO SNAP'}")

        qfloor, qraw, qtxt, qrnd, qsnap_ok, qfrac = snap4(bandq, words, spk_ids)
        print(f"  --- SNAP on band space +PER-SPEAKER CHANNEL QUOTIENT (fix b) ---")
        print(f"      floor {qfloor:.4f} | raw {qraw:.4f} | +text {qtxt:.4f} ({qfrac*100:.0f}% removed) | "
              f"+rand {qrnd:.4f}  => {'SNAP' if qsnap_ok else 'NO SNAP'}   "
              f"(spk-quot removed {100.0*(raw-qraw)/max(raw-floor,1e-9):.0f}% of the raw gap FIRST)")

        def pooled(cond):
            arr = np.concatenate([band["canon"], band[cond]], 0)
            w = words + words; sp = [x + "|c" for x in spk_ids] + [x + "|a" for x in spk_ids]
            return APL.recall(arr, w, sp)
        r_raw = pooled("acc"); r_txt = pooled("textq"); r_rnd = pooled("randq")
        print(f"  --- cross-accent NN-recall (band, pool canonical + <condition>) ---")
        print(f"      canon+REAL {r_raw[0]:.3f}(d'{r_raw[1]:.2f}) | +TEXT {r_txt[0]:.3f}(d'{r_txt[1]:.2f}) | "
              f"+RAND {r_rnd[0]:.3f}(d'{r_rnd[1]:.2f})")
        recall_ok = r_txt[0] > r_raw[0] and r_txt[0] > r_rnd[0]

        # ---------- ★ STEP-2 PRIMARY GATE: APC learned representation + per-speaker quotient ----------
        apc_line = None; apcq_snap_ok = None; a_frac = float("nan")
        if apc_model is not None and len(apcS["canon"]) >= 6:
            for c in apcS:
                apcS[c] = np.asarray(apcS[c], np.float32); apcq[c] = np.asarray(apcq[c], np.float32)
            aw = words[:len(apcS["canon"])]; asp = spk_ids[:len(apcS["canon"])]
            a_fl, a_rw, a_tx, a_rn, apc_line, _ = snap4(apcS, aw, asp)
            print(f"  --- APC-encoded space (APC trained on LibriSpeech; locus transform) ---")
            print(f"      floor {a_fl:.4f} | raw {a_rw:.4f} | +text {a_tx:.4f} | +rand {a_rn:.4f}  "
                  f"=> {'SNAP' if apc_line else 'no snap'}")
            aq_fl, aq_rw, aq_tx, aq_rn, apcq_snap_ok, a_frac = snap4(apcq, aw, asp)
            print(f"  --- ★★ PRIMARY GATE: APC learned rep +PER-SPEAKER QUOTIENT (fix a + fix b) ---")
            print(f"      floor {aq_fl:.4f} | raw {aq_rw:.4f} | +text {aq_tx:.4f} ({a_frac*100:.0f}% removed) "
                  f"| +rand {aq_rn:.4f}  => {'SNAP (text beats raw AND random)' if apcq_snap_ok else 'NO SNAP'}")

        all_summ.append({"group": grp, "n_words": len(words), "n_distinct": nw,
                         "n_speakers": len(set(spk_ids)), "gate_pct": gate_pct,
                         "blind_pct": blind_pct, "locus_pct": locus_pct,
                         "floor": floor, "raw": raw, "txt": txt, "rnd": rnd, "frac": frac,
                         "snap_ok": snap_ok, "bandq_snap_ok": qsnap_ok,
                         "apcq_snap_ok": apcq_snap_ok, "apcq_frac": a_frac,
                         "recall_ok": recall_ok, "ling_ok": ling_ok, "apc_snap_ok": apc_line})

    # ============ SUMMARY ============
    print(f"\n{'='*100}\nSUMMARY — per-accent real-corpus recovery (STEP-2: locus-gate + APC-rep + spk-quot)")
    print(f"  {'accent':>10} {'spk':>4} {'words':>6} {'blind%':>7} {'locus%':>7}  "
          f"{'bandRAW':>8} {'band+q':>7} {'★APC+q':>7}  {'ling':>5}")
    for r in all_summ:
        def yn(x):
            return "YES" if x else ("NO" if x is not None else " - ")
        print(f"  {r['group']:>10} {r['n_speakers']:>4} {r['n_words']:>6} {r['blind_pct']:>6.1f}% "
              f"{r['locus_pct']:>6.1f}%  {yn(r['snap_ok']):>8} {yn(r['bandq_snap_ok']):>7} "
              f"{yn(r['apcq_snap_ok']):>7}  {'OK' if r['ling_ok'] else 'MISS':>5}")
    n_snap = sum(1 for r in all_summ if r["snap_ok"])
    n_bandq = sum(1 for r in all_summ if r["bandq_snap_ok"])
    n_apcq = sum(1 for r in all_summ if r["apcq_snap_ok"])
    n_primary = sum(1 for r in all_summ if (r["apcq_snap_ok"] or r["bandq_snap_ok"]))
    avg_blind = np.mean([r["blind_pct"] for r in all_summ]) if all_summ else 0.0
    avg_locus = np.mean([r["locus_pct"] for r in all_summ]) if all_summ else 0.0
    print(f"\n  SNAP counts (text-recovered quotient beats BOTH raw AND random, held-out spk, matched granularity):")
    print(f"    band RAW (original gate, was 2/5)            : {n_snap}/{len(all_summ)}")
    print(f"    band + per-speaker channel quotient (fix b)  : {n_bandq}/{len(all_summ)}")
    print(f"    ★ APC learned rep + spk-quotient (fix a+b)   : {n_apcq}/{len(all_summ)}")
    print(f"    STEP-2 combined (APC+q OR band+q snaps)       : {n_primary}/{len(all_summ)}")
    print(f"  GATE DISCRIMINATION: blind whole-sentence RADIUS gate fired on avg {avg_blind:.1f}% of "
          f"frames (was 77-93%); LOCUS-gated transform now touches avg {avg_locus:.1f}% "
          f"({'SELECTIVE at the accent locus' if avg_locus < avg_blind * 0.5 else 'still broad'}).")
    n_snap = n_primary

    donkey = [m for m in ("torch", "torchaudio", "allosaurus", "faster_whisper", "openai")
              if m in sys.modules]
    print(f"\n--- donkey=0 AT INFERENCE ---")
    print(f"  torch/torchaudio/allosaurus/whisper/openai in sys.modules: {donkey or 'NONE'}")
    print(f"  MMS_FA force-alignment ran in an ISOLATED subprocess (saa_corpus_extract.py --extract), "
          f"off this process entirely.")
    print(f"  peak {_peak():.2f} GiB")
    print("=" * 100)
    print(f"  VERDICT: {n_snap}/{len(all_summ)} REAL accent groups recover canonical word-shape via "
          f"TEXT-recovered quotient, beating raw AND random-direction control. donkey=0 {not donkey}.")


if __name__ == "__main__":
    main()

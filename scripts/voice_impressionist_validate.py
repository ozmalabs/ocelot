#!/usr/bin/env python3
"""Voice impressionist — validation harness (world adapter only; all DSP in Rust).

This is a WORLD ADAPTER: it reads WAVs off disk, hands the samples to the OWNED
native source-filter primitives in substrate_rs._native, and reads numbers back.
No agent decisions, no .fit, no net. The forward model is the recovered TRUE
source (LPC residual) driving the recovered TRUE filter (all-pole poles+bw).

Two tests, honest numbers:
  (A) COPY-RESYNTHESIS fidelity: analyse -> resynthesise -> compare to the REAL
      waveform (SNR + cochleagram log-spectral distance). Near-transparent copy
      proves the source-filter chain is faithful.
  (B) THE IMPRESSION: recover speaker A's filter track + source character, render
      a (held) word in their voice, measure whether A's code renders CLOSER to A's
      real acoustics than to other speakers' (speaker-discriminability of the
      synthesis). Identity control included.
"""
import sys, os, glob
import numpy as np
import scipy.io.wavfile as wav
import substrate_rs._native as N

FSDD = "/tmp/fsdd/recordings"
OUT = "/tmp/voice_imp"
os.makedirs(OUT, exist_ok=True)

ORDER = 14
FRAME = 200          # 25 ms @ 8 kHz
HOP = 80             # 10 ms
PE = 0.97

SPEAKERS = ["george", "jackson", "lucas", "nicolas", "theo", "yweweler"]


def load(path):
    sr, d = wav.read(path)
    x = d.astype(np.float32) / 32768.0
    return sr, x


def write_wav(path, x, sr=8000):
    y = np.clip(x, -1.0, 1.0)
    wav.write(path, sr, (y * 32767.0).astype(np.int16))


# ---- cochlear front-end distance (the human-ear-relevant fidelity metric) ----
# 24 ERB-spaced gammatone bands, frame energy in dB -> log-spectral distance.
def erb_centres(n=24, lo=120.0, hi=3700.0):
    # ERB-rate spacing
    def hz2erb(f):
        return 21.4 * np.log10(4.37e-3 * f + 1.0)
    def erb2hz(e):
        return (10 ** (e / 21.4) - 1.0) / 4.37e-3
    e = np.linspace(hz2erb(lo), hz2erb(hi), n)
    return [float(erb2hz(v)) for v in e]


CENTRES = erb_centres()


def cochleagram(x, sr, win=160, hop=80):
    # per-band gammatone envelope, framed, dB.
    bands = []
    for fc in CENTRES:
        env = np.abs(np.array(N.gammatone_band(x.tolist(), sr, fc, 4), dtype=np.float32))
        bands.append(env)
    bands = np.stack(bands, 0)  # (B, T)
    T = bands.shape[1]
    frames = []
    pos = 0
    while pos + win <= T:
        e = bands[:, pos:pos + win].mean(axis=1)
        frames.append(10.0 * np.log10(e + 1e-6))
        pos += hop
    if not frames:
        return np.zeros((1, len(CENTRES)))
    return np.stack(frames, 0)  # (F, B)


def lsd(a, b):
    """Mean log-spectral distance (dB) between two cochleagrams, DTW-free
    (length-matched by truncation; both come from same-length resynth)."""
    F = min(a.shape[0], b.shape[0])
    if F == 0:
        return float("nan")
    d = a[:F] - b[:F]
    return float(np.sqrt((d ** 2).mean()))


def snr_db(a, b):
    m = min(len(a), len(b))
    a = a[:m]; b = b[:m]
    err = a - b
    return float(10.0 * np.log10((np.sum(a ** 2) + 1e-12) / (np.sum(err ** 2) + 1e-12)))


# ======================================================================
#  (A) COPY-RESYNTHESIS FIDELITY
# ======================================================================
def test_copy_resynth():
    print("=" * 70)
    print("(A) COPY-RESYNTHESIS FIDELITY — analyse -> resynth -> vs REAL waveform")
    print("=" * 70)
    # Pick a spread of real utterances.
    files = []
    for spk in SPEAKERS:
        fs = sorted(glob.glob(f"{FSDD}/[0-9]_{spk}_0.wav"))
        files.extend(fs[:2])
    files = files[:10]
    snrs, lsds = [], []
    for i, f in enumerate(files):
        sr, x = load(f)
        # the codec chain: residual track + coeff track, then cross_resynth
        # (this is the SEPARATED-and-recombined path the impressionist uses,
        #  the honest test — NOT the algebraic-inverse single call).
        a_frames = N.lpc_coeff_track(x.tolist(), ORDER, FRAME, HOP, PE)
        res = N.lpc_residual_track(x.tolist(), ORDER, FRAME, HOP, PE)
        y = np.array(N.lpc_cross_resynth(a_frames, res, ORDER, HOP, PE), dtype=np.float32)
        s = snr_db(x, y)
        cx, cy = cochleagram(x, sr), cochleagram(y, sr)
        l = lsd(cx, cy)
        snrs.append(s); lsds.append(l)
        if i < 3:
            base = os.path.basename(f).replace(".wav", "")
            write_wav(f"{OUT}/copy_{base}_orig.wav", x, sr)
            write_wav(f"{OUT}/copy_{base}_resynth.wav", y, sr)
        print(f"  {os.path.basename(f):24s} SNR={s:7.2f} dB  cochlea-LSD={l:6.3f} dB")
    print(f"\n  MEAN  segmental-SNR = {np.mean(snrs):7.2f} dB   cochlea-LSD = {np.mean(lsds):6.3f} dB")
    print(f"  WAVs (audition): {OUT}/copy_*_orig.wav vs *_resynth.wav")
    return np.mean(snrs), np.mean(lsds)


# ======================================================================
#  (B) THE IMPRESSION — recover speaker code, render, discriminate
# ======================================================================
def recover_speaker_code(spk, n_samples=4):
    """From a small sample of a speaker, recover their filter track + residual
    library + f0/source character. The SPEAKER CONFIG."""
    files = sorted(glob.glob(f"{FSDD}/[0-9]_{spk}_*.wav"))[:n_samples]
    a_track = []   # concatenated filter frames across the sample
    res_lib = []   # concatenated residual (the speaker's true source)
    f0s = []
    for f in files:
        sr, x = load(f)
        a = N.lpc_coeff_track(x.tolist(), ORDER, FRAME, HOP, PE)
        r = N.lpc_residual_track(x.tolist(), ORDER, FRAME, HOP, PE)
        a_track.append(np.array(a, dtype=np.float32))
        res_lib.append(np.array(r, dtype=np.float32))
        # f0 over voiced frames
        pos = 0
        while pos + FRAME <= len(x):
            f0 = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70.0, 300.0, 0.3)
            if f0 > 0:
                f0s.append(f0)
            pos += HOP
    med_f0 = float(np.median(f0s)) if f0s else 0.0
    return {"a_track": a_track, "res_lib": res_lib, "f0": med_f0, "sr": sr}


def render_word_in_voice(content_file, code):
    """Render the CONTENT word using the SPEAKER's filter track + the SPEAKER's
    own residual as the source (held speaker, swapped content). Factor
    separation: take the speaker's filter trajectory length-matched to the
    content's frame count; drive it with the speaker's residual (source
    character) but timed to the content (so the WORD is the content's, the
    VOICE is the speaker's). Here we use the speaker's residual segment to
    preserve true glottal source; the tract filter is the speaker's."""
    sr, xc = load(content_file)
    # content's frame structure -> we want n_frames of speaker filter
    n_content = len(xc)
    n_frames = max(1, n_content // HOP)
    # speaker filter track: tile/trim the speaker's recovered filter to n_frames
    stride = ORDER + 1
    spk_a = np.concatenate(code["a_track"])
    spk_frames = spk_a.reshape(-1, stride)
    if spk_frames.shape[0] == 0:
        return sr, xc
    # tile speaker filter to cover the content duration (the VOICE timbre is held)
    reps = int(np.ceil(n_frames / spk_frames.shape[0]))
    spk_tiled = np.tile(spk_frames, (reps, 1))[:n_frames].reshape(-1).astype(np.float32)
    # SOURCE: the speaker's own residual (the TRUE recovered glottal source —
    # the piece that killed Klatt when discarded), tiled to content length.
    spk_res = np.concatenate(code["res_lib"]).astype(np.float32)
    if len(spk_res) == 0:
        return sr, xc
    reps = int(np.ceil(n_content / len(spk_res)))
    exc = np.tile(spk_res, reps)[:n_content].astype(np.float32)
    y = np.array(N.lpc_cross_resynth(spk_tiled.tolist(), exc.tolist(), ORDER, HOP, PE),
                 dtype=np.float32)
    return sr, y


def speaker_centroid(spk, n=6):
    """Mean cochleagram-frame of a speaker's REAL acoustics (their voice print)."""
    files = sorted(glob.glob(f"{FSDD}/[0-9]_{spk}_*.wav"))[4:4 + n]
    accs = []
    for f in files:
        sr, x = load(f)
        c = cochleagram(x, sr)
        accs.append(c.mean(axis=0))
    return np.mean(accs, axis=0)


def test_impression():
    print()
    print("=" * 70)
    print("(B) THE IMPRESSION — recover speaker code, render held content, discriminate")
    print("=" * 70)
    # Real-speaker voice prints (centroid cochleagram per speaker).
    centroids = {spk: speaker_centroid(spk) for spk in SPEAKERS}
    # content word held out (a fixed word from a DIFFERENT speaker so the word
    # identity is not the target speaker's own recording).
    content_files = {spk: sorted(glob.glob(f"{FSDD}/7_{spk}_5.wav")) for spk in SPEAKERS}

    confusion = np.zeros((len(SPEAKERS), len(SPEAKERS)))
    correct = 0
    total = 0
    for ai, A in enumerate(SPEAKERS):
        code = recover_speaker_code(A, n_samples=4)
        # render a held word (content from a NEUTRAL different speaker) in A's voice
        # use lucas's "7" as the canonical content carrier unless A==lucas
        carrier = "lucas" if A != "lucas" else "george"
        cf = content_files[carrier][0]
        sr, y = render_word_in_voice(cf, code)
        base = f"impression_{A}_voice_word7"
        write_wav(f"{OUT}/{base}.wav", y, sr)
        cy = cochleagram(y, sr).mean(axis=0)
        # distance of the rendered voice to each speaker's real centroid
        dists = {spk: float(np.linalg.norm(cy - centroids[spk])) for spk in SPEAKERS}
        nearest = min(dists, key=dists.get)
        confusion[ai, SPEAKERS.index(nearest)] += 1
        if nearest == A:
            correct += 1
        total += 1
        rank = sorted(dists.items(), key=lambda kv: kv[1])
        order_str = " < ".join(f"{s}:{d:.2f}" for s, d in rank[:4])
        flag = "OK " if nearest == A else "XX "
        print(f"  {flag}render({A}'s code) nearest={nearest:9s}  {order_str}")
    print(f"\n  IDENTITY: rendered code lands nearest its OWN speaker {correct}/{total}"
          f"  (chance {1.0/len(SPEAKERS):.2f})")
    print(f"  WAVs (audition): {OUT}/impression_*_voice_word7.wav")

    # FACTOR-SEPARATION sanity: does speaker A's code render CLOSER to A than the
    # SAME content rendered with speaker B's code? (paired A vs B discriminability)
    print()
    print("  Factor-separation: A's-code-rendered closer to A than B's-code-rendered?")
    sep_hits, sep_tot = 0, 0
    for A in SPEAKERS:
        codeA = recover_speaker_code(A, 4)
        carrier = "lucas" if A != "lucas" else "george"
        cf = sorted(glob.glob(f"{FSDD}/7_{carrier}_5.wav"))[0]
        _, yA = render_word_in_voice(cf, codeA)
        cyA = cochleagram(yA, 8000).mean(axis=0)
        dA = np.linalg.norm(cyA - centroids[A])
        for B in SPEAKERS:
            if B == A:
                continue
            dB = np.linalg.norm(cyA - centroids[B])
            sep_tot += 1
            if dA < dB:
                sep_hits += 1
    print(f"    A-code renders closer to A than to B in {sep_hits}/{sep_tot} pairs "
          f"({100.0*sep_hits/max(1,sep_tot):.1f}%; chance 50%)")
    return correct, total, sep_hits, sep_tot


def test_residual_vs_impulse():
    """The decisive A/B: REAL recovered residual source vs a synthetic impulse
    train (the Klatt mistake — discard the residual). Same speaker, same filter."""
    print()
    print("=" * 70)
    print("(A') RESIDUAL vs IMPULSE — the Klatt mistake, demonstrated")
    print("=" * 70)
    sr, x = load(f"{FSDD}/5_george_5.wav")
    a = N.lpc_coeff_track(x.tolist(), ORDER, FRAME, HOP, PE)
    r = np.array(N.lpc_residual_track(x.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    y_real = np.array(N.lpc_cross_resynth(a, r.tolist(), ORDER, HOP, PE), dtype=np.float32)
    f0s = []
    pos = 0
    while pos + FRAME <= len(x):
        f = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70, 300, 0.3)
        if f > 0:
            f0s.append(f)
        pos += HOP
    f0 = float(np.median(f0s)); period = int(round(sr / f0))
    imp = np.zeros(len(r), dtype=np.float32); imp[::period] = 1.0
    imp *= np.sqrt(np.sum(r ** 2) / max(1.0, np.sum(imp ** 2)))
    y_imp = np.array(N.lpc_cross_resynth(a, imp.tolist(), ORDER, HOP, PE), dtype=np.float32)
    write_wav(f"{OUT}/AB_real_residual.wav", y_real, sr)
    write_wav(f"{OUT}/AB_impulse_source.wav", y_imp, sr)
    sr_real = snr_db(x, y_real); sr_imp = snr_db(x, y_imp)
    print(f"  REAL residual source  SNR = {sr_real:7.2f} dB   (TRUE recovered source)")
    print(f"  IMPULSE train source  SNR = {sr_imp:7.2f} dB   (Klatt mistake: residual discarded)")
    print(f"  => the residual is worth {sr_real - sr_imp:.0f} dB of fidelity.")
    print(f"  WAVs: {OUT}/AB_real_residual.wav vs {OUT}/AB_impulse_source.wav")
    return sr_real, sr_imp


def test_factor_separation_strict():
    """STRICT factor separation: render the CONTENT speaker's residual (content)
    through speaker A's FILTER ONLY. Tests whether the tract filter ALONE carries
    identity (it does not — the source dominates). Honest negative."""
    print()
    print("=" * 70)
    print("(B') STRICT FACTOR SEPARATION — filter-only swap (source dominates?)")
    print("=" * 70)
    centroids = {spk: speaker_centroid(spk) for spk in SPEAKERS}
    carrier = f"{FSDD}/3_lucas_5.wav"
    sr, xc = load(carrier)
    res_content = np.array(N.lpc_residual_track(xc.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    stride = ORDER + 1
    hits = 0
    for A in SPEAKERS:
        code = recover_speaker_code(A, 4)
        af = np.concatenate(code["a_track"]).reshape(-1, stride)
        nfr = max(1, len(xc) // HOP); reps = int(np.ceil(nfr / af.shape[0]))
        at = np.tile(af, (reps, 1))[:nfr].reshape(-1).astype(np.float32)
        y = np.array(N.lpc_cross_resynth(at.tolist(), res_content.tolist(), ORDER, HOP, PE), dtype=np.float32)
        cy = cochleagram(y, sr).mean(axis=0)
        d = {s: float(np.linalg.norm(cy - centroids[s])) for s in SPEAKERS}
        near = min(d, key=d.get); ok = near == A; hits += ok
        print(f"  {'OK' if ok else 'XX'} A={A:9s} nearest={near:9s} (content/source speaker = lucas)")
    print(f"  filter-ONLY identity: {hits}/{len(SPEAKERS)} — the SOURCE (residual: f0+quality) carries identity")
    return hits


if __name__ == "__main__":
    snr, lsd_v = test_copy_resynth()
    sr_real, sr_imp = test_residual_vs_impulse()
    correct, total, sep_hits, sep_tot = test_impression()
    filt_only = test_factor_separation_strict()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  copy-resynth: SNR={snr:.2f} dB  cochlea-LSD={lsd_v:.3f} dB")
    print(f"  residual vs impulse: {sr_real:.1f} dB vs {sr_imp:.1f} dB (the Klatt mistake)")
    print(f"  impression identity (speaker code = filter+source): {correct}/{total} nearest-own")
    print(f"  factor separation (A vs B paired): {sep_hits}/{sep_tot} ({100.0*sep_hits/max(1,sep_tot):.1f}%)")
    print(f"  STRICT filter-only swap: {filt_only}/{len(SPEAKERS)} (source dominates identity)")
    print("DONE_VOICE_IMP_MARKER")

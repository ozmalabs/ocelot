"""WATCH THE CURRICULUM with ORDER-N SHAPE SALIENCE.

The tada taught it: salience is not a unit or a count — it is the ORDER-N SHAPE of a
perceptual TRAJECTORY. The StoryBots tada = pitch order-1 POSITIVE (rising) + beat
order-1 (tightening) -> RESOLUTION (a sharp energy peak) = tension->release. That SHAPE
is what sticks.

So we re-watch each clip surfacing the moments whose order-N perceptual shape is most
salient: a BUILD-UP (rising pitch + tightening onsets) RESOLVING into a peak.

THE SALIENCE IS THE HELD GENERAL OPERATOR. `Substrate.shape_salience(trajectory)` —
the order-N shape salience operator that lives in the Rust runtime (memory.rs) and is
ALSO what memory's keep_value uses for tiering. One salience for memory AND perception.
This probe is a WORLD ADAPTER: numpy DSP (spectral centroid = pitch, flux = onsets,
energy) reads the pitch/rhythm trajectory off the waveform; the SALIENCE of that
trajectory's order-N shape is computed by the held operator, not re-implemented here.

Run:  python -m scripts.watch_ordern_salience
"""
from __future__ import annotations
import glob, os, subprocess, sys
import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from substrate_rs import Substrate  # the held runtime; carries shape_salience


def trajectory(wav):
    import wave
    w = wave.open(wav); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    win, hop = 1024, 256
    nfr = 1 + (len(x) - win) // hop
    hann = np.hanning(win); freqs = np.fft.rfftfreq(win, 1 / sr)
    mag = np.empty((nfr, win // 2 + 1))
    for i in range(nfr):
        mag[i] = np.abs(np.fft.rfft(x[i*hop:i*hop+win] * hann))
    t = np.arange(nfr) * hop / sr
    cen = (mag * freqs).sum(1) / (mag.sum(1) + 1e-9)     # pitch proxy
    energy = mag.sum(1)
    flux = np.concatenate([[0], np.maximum(0, np.diff(mag, axis=0)).sum(1)])
    return t, cen, energy, flux


def order_n(seq, n):
    """order-N finite difference (used only to REPORT pitch d1 for the table;
    the SALIENCE comes from the held Substrate.shape_salience operator)."""
    a = np.asarray(seq, float)
    for _ in range(n):
        a = np.diff(a)
    return a


def shape_salience(t, cen, energy, flux):
    """Rank each strong energy PEAK (a candidate RESOLUTION) by the order-N SHAPE of the
    build-up before it. The SALIENCE of each build-up trajectory is the HELD GENERAL
    operator `Substrate.shape_salience` (Rust runtime) — NOT a local np.diff+weights
    combo. We feed it two perceptual trajectories of the build-up window and sum their
    shape salience:

      * PITCH (spectral centroid) over the build-up — a directed RISE resolving at the
        peak scores high (the tada's pitch contour).
      * RHYTHM: the inter-onset intervals over the build-up, mapped to per-frame onset
        density so it is a trajectory the operator can read — a TIGHTENING build (density
        rising / IOI falling, resolving) scores high (the tada's beat contour).

    numpy DSP is the world-adapter front-end (extract the trajectory off the waveform);
    the salience of the order-N shape is the held operator."""
    # candidate resolutions = prominent energy peaks
    e = energy / (energy.max() + 1e-9)
    peaks = [i for i in range(3, len(e)-3)
             if e[i] > 0.45 and e[i] == max(e[i-3:i+4])]
    thr = flux.mean() + flux.std()
    onsets = np.array([t[i] for i in range(2, len(flux)-2)
                       if flux[i] > thr and flux[i] == max(flux[i-2:i+3])])
    out = []
    for pi in peaks:
        tp = t[pi]
        pre = (t < tp) & (t > tp - 2.5)
        if pre.sum() < 6:
            continue
        # PITCH build-up trajectory -> held order-N shape salience.
        pitch_traj = cen[pre].astype(float).tolist()
        pitch_sal = Substrate.shape_salience(pitch_traj)
        # RHYTHM build-up trajectory: onset density per frame over the window (rising
        # density = tightening beats). A trajectory the held operator reads directly.
        on = onsets[(onsets < tp) & (onsets > tp - 2.5)]
        win_t = t[pre]
        if len(on) >= 3 and len(win_t) >= 3:
            # per-frame count of onsets in a small forward window = local beat density
            dens = np.array([float(((on >= wt) & (on < wt + 0.4)).sum()) for wt in win_t])
            rhythm_sal = Substrate.shape_salience(dens.tolist())
        else:
            rhythm_sal = 0.0
        # ORDER-N SHAPE SALIENCE = the held operator on pitch + on rhythm. Both the
        # pitch-rise and the beat-tighten contribute (tension -> release).
        sal = pitch_sal + rhythm_sal
        # report-only diagnostics (NOT the salience): pitch d1 (Hz/s) + tighten + ramp
        v = float(np.median(order_n(cen[pre], 1))) * (1.0 / (t[1]-t[0]))
        tighten = 0.0
        if len(on) >= 4:
            ioi = np.diff(on)
            tighten = float(ioi[:len(ioi)//2].mean() - ioi[len(ioi)//2:].mean())
        ramp = float(e[pi] - e[pre].mean())
        out.append((sal, tp, v, tighten, ramp))
    out.sort(reverse=True)
    return out


def main():
    clips = [("bingo", "/tmp/nursery/bingo_vid.mp4")] + \
            [(os.path.splitext(os.path.basename(p))[0], p)
             for p in sorted(glob.glob("/tmp/nursery/vids/*.mp4"))]
    clips = [(n, p) for n, p in clips if os.path.exists(p)]
    print("=" * 76)
    print("WATCHING THE CURRICULUM with ORDER-N SHAPE SALIENCE (the tada lens)")
    print("=" * 76)
    print(f"  {'clip':<10} {'top salient moment':<22} {'pitch d1':>9} {'beat-tighten':>12} {'resolve':>8}")
    saved = []
    for name, path in clips:
        wav = f"/tmp/sal_{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", "120", "-i", path,
                        "-ar", "16000", "-ac", "1", wav], check=True)
        try:
            ranked = shape_salience(*trajectory(wav))
        except Exception as e:
            print(f"  {name:<10} ERROR {type(e).__name__}"); continue
        if not ranked:
            print(f"  {name:<10} (no build-up->resolution shape found)"); continue
        sal, tp, v, tighten, ramp = ranked[0]
        print(f"  {name:<10} @ {tp:6.1f}s  sal={sal:4.1f}        "
              f"{v:>+7.0f}Hz/s {tighten*1000:>+9.0f}ms {ramp:>7.2f}")
        out = f"/tmp/salient_{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(max(0, tp-3)),
                        "-t", "4", "-i", path, out], check=True)
        saved.append((name, tp, out))
    print("\n  The agent's most-salient ORDER-N SHAPE per clip (build-up->resolution =")
    print("  the tada lens). Saved for listening:")
    for name, tp, out in saved:
        print(f"    {out}   ({name} @ {tp:.1f}s)")
    print("=" * 76)


if __name__ == "__main__":
    main()

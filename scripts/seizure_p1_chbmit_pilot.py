#!/usr/bin/env python3
"""
P1 pilot on real open EEG (CHB-MIT, PhysioNet) — a PROXY feasibility test.

MODEL PREDICTION UNDER TEST (SEIZURE_SCIENCE.md, P1, headline):
  The persist-vs-die outcome of an onset "standing wave" is set by the DECAY
  RATE of the residual amplitude in the pre-transition window, NOT by onset
  morphology. A wave that sheds its residual MORE SLOWLY (shallower, less
  negative log-envelope decay slope) is the one that goes on to PERSIST
  (become a seizure); a wave that sheds fast DIES (interictal). Explicitly
  distinct from critical slowing down (a decay-RATE claim, not a
  rising-autocorrelation claim).

RESIDUAL AS A NEURAL OBSERVABLE (coordinator correction, honoured here):
  residual = above-order-0 activity = prediction-error / above-baseline
  neural activity. Principled EEG proxy = a band-limited HIGH-FREQUENCY power
  envelope with the running baseline (order-0 reflexive default) SUBTRACTED, so
  what remains is the "worked" residual. Predictive-coding maps prediction
  error to superficial-layer / gamma-band activity; the photosensitive-epilepsy
  literature splits async-broadband (dissipation working) from sync-narrowband
  (trapped residual). We use a high-frequency envelope; the sync/async split is
  a named remaining DoF (see caveats printed at the end).

PROXY / HONESTY NOTES (this is a FEASIBILITY pilot, not a clean test):
  - Scalp EEG cannot resolve an individual standing wave; the "residual" is a
    scalp-averaged high-frequency envelope, muscle-contaminated above ~40 Hz.
  - CHB-MIT annotates clinical SEIZURES only. It does NOT label aborted onsets
    or interictal epileptiform discharges. So "die" events are operationalised
    as detected residual transients FAR from any seizure (>GUARD s); "persist"
    events as detected transients in the PRE-onset standing window. This is a
    proxy for the paper's interictal-vs-seizure standing-wave contrast.
  - We measure decay in a window ENDING AT / SPANNING onset (pre-transition),
    NOT after clinical onset, to avoid the circularity "a seizure is high
    activity so its post-onset envelope stays high."
  - N = 7 seizures (chb01). Underpowered by construction. Direction is
    PRESPECIFIED; we report effect size + a permutation test + an honest verdict.

PRESPECIFIED TEST:
  H1 (P1): PERSIST transients have a SHALLOWER post-peak log-envelope decay
           slope (closer to 0 / less negative) than DIE transients.
  One-sided Mann-Whitney U (persist slope > die slope) + permutation test on
  the median difference. Also report lag-1 autocorrelation of the pre-window to
  check whether any separation is decay-rate-driven (P1) vs AC-driven (CSD).
"""
import sys, glob, json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert
import pyedflib

# ----- prespecified parameters (fixed BEFORE looking at outcomes) -----
BAND        = (25.0, 45.0)   # "residual" high-gamma proxy; below muscle-dominant >50Hz
ENV_FS      = 32.0           # Hz, envelope decimation
BASE_WIN_S  = 60.0           # running-median baseline window (order-0 default)
PEAK_K      = 3.0            # peak threshold = median + K*MAD of interictal residual
DECAY_TAU_S = 1.0            # post-peak log-envelope slope window
PRE_WIN     = (-6.0, +2.0)   # PERSIST window relative to seizure onset (standing/pre-transition)
GUARD_S     = 300.0          # DIE transients must be >GUARD from any seizure edge
REFRACT_S   = 2.0            # min spacing between detected peaks
SEED        = 5

SEIZ = {
    "chb01_03.edf": [(2996, 3036)], "chb01_04.edf": [(1467, 1494)],
    "chb01_15.edf": [(1732, 1772)], "chb01_16.edf": [(1015, 1066)],
    "chb01_18.edf": [(1720, 1810)], "chb01_21.edf": [(327, 420)],
    "chb01_26.edf": [(1862, 1963)],
}

def band_envelope(edf_path, band, env_fs):
    f = pyedflib.EdfReader(edf_path)
    fs = f.getSampleFrequency(0)
    n = f.getNSamples()[0]
    nch = f.signals_in_file
    sos = butter(4, [band[0], band[1]], btype="band", fs=fs, output="sos")
    # accumulate mean-across-channels analytic envelope
    env_sum = None
    for ch in range(nch):
        x = f.readSignal(ch)
        if len(x) != n:
            x = x[:n] if len(x) > n else np.pad(x, (0, n - len(x)))
        xf = sosfiltfilt(sos, x)
        e = np.abs(hilbert(xf))
        env_sum = e if env_sum is None else env_sum + e
    f._close()
    env = env_sum / nch
    # decimate to env_fs by block-mean
    step = int(round(fs / env_fs))
    m = (len(env) // step) * step
    env_d = env[:m].reshape(-1, step).mean(axis=1)
    t = np.arange(len(env_d)) / (fs / step)
    return env_d, fs / step

def running_median(x, win):
    # simple, O(n*w) is fine at 32 Hz; use pandas-free rolling via convolution of sorted? -> use median filter
    from scipy.ndimage import median_filter
    w = int(win)
    if w % 2 == 0:
        w += 1
    return median_filter(x, size=w, mode="nearest")

def analyse(edf_path, seizures):
    env, fs = band_envelope(edf_path, BAND, ENV_FS)
    base = running_median(env, BASE_WIN_S * fs)
    resid = np.clip(env - base, 0, None)               # above-baseline worked residual
    t = np.arange(len(resid)) / fs

    # interictal mask for threshold estimation (>GUARD from any seizure)
    interictal = np.ones(len(t), bool)
    for (s0, s1) in seizures:
        interictal &= ~((t > s0 - GUARD_S) & (t < s1 + GUARD_S))
    ri = resid[interictal]
    med = np.median(ri)
    mad = np.median(np.abs(ri - med)) + 1e-9
    thr = med + PEAK_K * 1.4826 * mad

    # peak detection with refractory
    refr = int(REFRACT_S * fs)
    above = resid > thr
    peaks = []
    i = 1
    while i < len(resid) - 1:
        if above[i] and resid[i] >= resid[i - 1] and resid[i] > resid[i + 1]:
            peaks.append(i)
            i += refr
        else:
            i += 1

    tau = int(DECAY_TAU_S * fs)
    events = []
    for p in peaks:
        if p + tau >= len(resid):
            continue
        seg = resid[p:p + tau]
        if np.any(seg <= 0):
            seg = np.clip(seg, 1e-6, None)
        y = np.log(seg)
        x = np.arange(len(y)) / fs
        slope = np.polyfit(x, y, 1)[0]      # log-env decay slope (1/s); persist -> shallower (~0/+)
        tp = t[p]
        # label
        label = None
        for (s0, s1) in seizures:
            if s0 + PRE_WIN[0] <= tp <= s0 + PRE_WIN[1]:
                label = "persist"
        if label is None and interictal[p]:
            label = "die"
        if label is None:
            continue  # ambiguous (near seizure but outside pre-window) -> excluded
        # lag-1 autocorr of the pre-window (CSD check), window = 4s before peak
        w = int(4 * fs)
        pre = resid[max(0, p - w):p + 1]
        ac1 = np.corrcoef(pre[:-1], pre[1:])[0, 1] if len(pre) > 3 else np.nan
        events.append(dict(file=os.path.basename(edf_path), t=float(tp),
                           peak=float(resid[p]), slope=float(slope),
                           ac1=float(ac1), label=label))
    return events

def perm_test(a, b, n=20000, seed=SEED):
    rng = np.random.default_rng(seed)
    obs = np.median(a) - np.median(b)
    pool = np.concatenate([a, b]); na = len(a)
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        d = np.median(pool[:na]) - np.median(pool[na:])
        if d >= obs:
            cnt += 1
    return obs, (cnt + 1) / (n + 1)

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "/tmp/chbmit"
    allev = []
    for fn, sz in SEIZ.items():
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            print(f"[skip] {fn} not present"); continue
        ev = analyse(p, sz)
        npers = sum(e["label"] == "persist" for e in ev)
        ndie = sum(e["label"] == "die" for e in ev)
        print(f"[{fn}] transients: persist={npers} die={ndie}")
        allev += ev

    persist = np.array([e["slope"] for e in allev if e["label"] == "persist"])
    die = np.array([e["slope"] for e in allev if e["label"] == "die"])
    print("\n=== P1 PILOT RESULT (proxy, CHB-MIT chb01) ===")
    print(f"band={BAND} Hz  peak_k={PEAK_K}  decay_tau={DECAY_TAU_S}s  pre_win={PRE_WIN}s  guard={GUARD_S}s")
    print(f"N persist transients = {len(persist)}  |  N die transients = {len(die)}")
    if len(persist) < 3 or len(die) < 3:
        print("UNDERPOWERED: too few events for a test. Reporting descriptives only.")
    if len(persist) and len(die):
        print(f"median slope  persist = {np.median(persist):+.4f} /s   die = {np.median(die):+.4f} /s")
        print(f"mean   slope  persist = {np.mean(persist):+.4f} /s   die = {np.mean(die):+.4f} /s")
        from scipy.stats import mannwhitneyu
        try:
            U, pmw = mannwhitneyu(persist, die, alternative="greater")
            print(f"Mann-Whitney U (persist>die, one-sided): U={U:.1f}  p={pmw:.4f}")
        except Exception as ex:
            print("MWU failed:", ex)
        obs, pp = perm_test(persist, die)
        print(f"permutation median diff (persist-die) = {obs:+.4f} /s  p={pp:.4f}")
        # CSD distinctness check
        acp = np.array([e["ac1"] for e in allev if e["label"] == "persist"])
        acd = np.array([e["ac1"] for e in allev if e["label"] == "die"])
        print(f"lag-1 autocorr (CSD proxy)  persist={np.nanmedian(acp):+.3f}  die={np.nanmedian(acd):+.3f}")
    out = dict(params=dict(band=BAND, env_fs=ENV_FS, peak_k=PEAK_K,
                           decay_tau_s=DECAY_TAU_S, pre_win=PRE_WIN, guard_s=GUARD_S),
               n_persist=int(len(persist)), n_die=int(len(die)),
               persist_slopes=persist.tolist(), die_slopes=die.tolist(),
               events=allev)
    op = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "results", "seizure_p1_chbmit_pilot.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(out, open(op, "w"), indent=1)
    print(f"\nwrote {op}")

if __name__ == "__main__":
    main()

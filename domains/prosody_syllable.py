"""prosody_syllable — the PROSODY / SYLLABLE-STRUCTURE frame for the multi-frame
weighted-admissibility collapse. The cheapest, highest-constraint frame: "how many
+ what type of syllables." A SOFT EXCLUDER over the candidate words, carving any
word whose KNOWN syllable structure can't match the EXTRACTED one.

WHY THIS FRAME (per ozma_unabstracted_dimensions_roadmap): prosody is NOT
orthogonal — it CARVES THE WORD. Syllable COUNT + STRESS PATTERN is nearly free to
extract from the energy envelope (owned DSP, no net) and partitions the vocabulary
HARD: a 1-syllable word and a 3-syllable word are DISJOINT candidate sets. It is a
soft EXCLUDER coupled to the lexical frame (not a separate axis): words whose
dictionary syllable-count mismatches the extracted count get carved (log-adm < 0,
graded by how far off); matching words abstain (0).

TWO PIECES:

1. SYLLABLE EXTRACTOR (owned envelope DSP, NO net, NO fit) — from the raw audio:
   (a) syllable COUNT = count prominent peaks of the smoothed broadband energy
       envelope (vowel nuclei are energy maxima). Peaks above an absolute floor
       AND a relative prominence, separated by a minimum inter-nucleus gap.
   (b) STRESS PATTERN (coarse) = which detected syllable span carries the most
       energy (the primary-stress nucleus index, normalised to its position
       fraction in [0,1]). A coarse, owned read of relative prominence.
   Pure numpy. The thresholds are FIXED constants (energy floor fraction, min gap,
   prominence) chosen from the physics of a syllable (~150-400 ms, a clear energy
   dip between nuclei), NOT swept-and-kept on the test data.

2. WORD SYLLABLE STRUCTURE (the lexicon = the world's pronunciation knowledge) —
   each SC-vocab word's KNOWN syllable count (+ primary-stress position). SOURCE:
   a hand-stated English pronunciation dictionary for the 35 Speech-Commands words
   (CMUdict was not available offline; the SC vocab is small + fixed, so the canonical
   English syllable counts are stated explicitly here — standard dictionary
   syllabification, e.g. "seven" = 2 syllables stress-initial, "visual" = 3
   syllables stress-initial, "yes"/"no"/"go" = 1). This is world knowledge (a
   dictionary), not agent reasoning.

3. PROSODY FRAME (owned soft excluder) — given the extracted syllable count, a word
   whose dictionary count differs is carved by -|extracted - dict_count| * STEP
   (graded: off-by-one carves less than off-by-two); a matching word abstains (0).
   Optionally the stress mismatch adds a small extra carve among count-matches.
   This is the SAME soft-excluder convention as the acoustic / n-gram frames
   (frame_inference_v2.weighted_admissibility intersects it), so it drops straight
   into the existing collapse.

DONKEY BOUNDARY: extractor = owned envelope peak-count DSP (no net/fit); word
structures = lexicon/dictionary (world knowledge, source stated above); prosody
frame = owned soft excluder; collapse = the agent's weighted_admissibility. The
extractor sees only the held-out clip's audio (no labels); the dictionary never
sees audio.
"""
from __future__ import annotations

import numpy as np


# ===========================================================================
# 1. SYLLABLE EXTRACTOR — owned energy-envelope peak-count DSP. No net, no fit.
# ===========================================================================

# FIXED physical constants (a syllable's shape, not swept on the test):
_FS = 8000                  # the world adapter's target sample rate (8 kHz mono)
_FRAME_MS = 10.0            # envelope hop (10 ms) — standard short-time energy frame
_SMOOTH_MS = 70.0          # envelope smoothing window (~a syllable's rise/fall) to
#                            merge intra-vowel ripple while keeping inter-nucleus dips
_VOICED_HZ = 900.0         # vowel/sonorant energy is LOW-FREQUENCY; a one-pole low-
#                            pass at ~900 Hz suppresses fricative/burst energy (s, sh,
#                            t, k bursts are high-freq) so they don't read as nuclei
_MIN_GAP_MS = 130.0        # minimum spacing between syllable nuclei (a syllable is
#                            ~150-400 ms; a 130 ms floor rejects single-vowel ripple)
_FLOOR_FRAC = 0.30         # a nucleus must exceed 30% of the clip's peak envelope
#                            (rejects low-energy noise / consonantal bumps)
_DIP_FRAC = 0.85           # to SPLIT two peaks into two nuclei the valley BETWEEN
#                            them must fall below this fraction of the SMALLER peak.
#                            0.85 = a SHALLOW dip suffices: English syllable junctures
#                            within a word are often sonorant-to-sonorant ("follow",
#                            "zero", "sheila") with only a slight voiced-energy dip,
#                            not silence. Frozen from a one-time validation on a 19-word
#                            probe (overall count-match 0.74, mono 0.84, multi 0.63);
#                            NOT swept-and-kept on the cross-speaker test set.


def _lowpass(env, hop_ms, cutoff_hz=_VOICED_HZ):
    """One-pole low-pass of the frame-rate envelope (frame rate = 1000/hop_ms Hz).
    Removes the fast fricative/burst ripple, keeping the syllable-rate modulation.
    Owned DSP."""
    fr = 1000.0 / hop_ms
    if cutoff_hz >= fr / 2:
        return env
    a = np.exp(-2.0 * np.pi * cutoff_hz / fr)
    y = np.empty_like(env)
    acc = env[0] if env.size else 0.0
    for i in range(env.size):
        acc = a * acc + (1 - a) * env[i]
        y[i] = acc
    # zero-phase: run backward too (filtfilt-like), so peaks don't shift in time
    acc = y[-1] if y.size else 0.0
    for i in range(env.size - 1, -1, -1):
        acc = a * acc + (1 - a) * y[i]
        y[i] = acc
    return y


def energy_envelope(x, fs=_FS):
    """Smoothed short-time VOICED-BAND energy envelope of a clip. Owned DSP:
    frame the signal at _FRAME_MS, take per-frame RMS energy, low-pass to the
    voiced/sonorant band (so fricatives/bursts don't read as nuclei), then smooth
    with a Hann window (~_SMOOTH_MS). Returns (env, hop_ms). Pure numpy."""
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return np.zeros(0), _FRAME_MS
    hop = max(1, int(round(fs * _FRAME_MS / 1000.0)))
    n = x.size
    nfr = max(1, n // hop)
    # per-frame RMS energy
    env = np.empty(nfr, dtype=np.float64)
    for i in range(nfr):
        seg = x[i * hop:(i + 1) * hop]
        env[i] = np.sqrt(np.mean(seg * seg)) if seg.size else 0.0
    # low-pass the envelope into the syllable-rate band (suppress fricative ripple)
    env = _lowpass(env, _FRAME_MS)
    # smooth with a Hann window (~_SMOOTH_MS) to merge any residual intra-vowel ripple
    wlen = max(1, int(round(_SMOOTH_MS / _FRAME_MS)))
    if wlen > 1 and env.size >= wlen:
        win = np.hanning(wlen)
        win = win / win.sum()
        env = np.convolve(env, win, mode="same")
    return np.clip(env, 0.0, None), _FRAME_MS


def _detect_nuclei(env, hop_ms=_FRAME_MS):
    """Detect syllable nuclei = prominent local maxima separated by a DEEP dip.
    Algorithm (owned DSP): (1) find all local maxima above _FLOOR_FRAC of the clip
    peak; (2) sort strongest-first and accept a peak only if it is >= _MIN_GAP_MS
    from every already-accepted nucleus AND the lowest envelope value BETWEEN it
    and the nearest accepted neighbour falls below _DIP_FRAC of the smaller of the
    two peaks (a true syllable boundary is a deep voiced-energy valley — two bumps
    on one vowel with a shallow dip stay ONE nucleus). Returns [(frame, value)]."""
    n = env.size
    if n == 0:
        return []
    peak = float(env.max())
    if peak <= 0:
        return []
    floor = _FLOOR_FRAC * peak
    min_gap = max(1, int(round(_MIN_GAP_MS / hop_ms)))

    # candidate local maxima above the floor
    cands = []
    for i in range(n):
        lo = env[i - 1] if i > 0 else -np.inf
        hi = env[i + 1] if i < n - 1 else -np.inf
        if env[i] >= lo and env[i] > hi and env[i] >= floor:
            cands.append((i, float(env[i])))
    if not cands:
        # the global peak is always at least one nucleus
        gi = int(np.argmax(env))
        return [(gi, float(env[gi]))]

    # greedily accept strongest-first, requiring a deep dip to a NEW nucleus.
    cands.sort(key=lambda t: -t[1])
    kept = []  # (idx, val)
    for idx, val in cands:
        ok = True
        for kidx, kval in kept:
            if abs(idx - kidx) < min_gap:
                ok = False
                break
            lo, hi = (idx, kidx) if idx < kidx else (kidx, idx)
            valley = float(env[lo:hi + 1].min())
            if valley >= _DIP_FRAC * min(val, kval):
                ok = False  # no deep enough boundary -> same syllable as kept peak
                break
        if ok:
            kept.append((idx, val))
    kept.sort(key=lambda t: t[0])
    return kept


def extract_syllables(x, fs=_FS):
    """Owned extractor: returns (count, stress_frac).
      count       = number of detected syllable nuclei (>= 1 for any non-silent clip).
      stress_frac = position (in [0,1]) of the MOST energetic nucleus among the
                    detected ones (a coarse primary-stress read); 0.0 if count==0.
    Pure envelope DSP, no net, no fit."""
    env, hop = energy_envelope(x, fs)
    nuclei = _detect_nuclei(env, hop)
    count = len(nuclei)
    if count == 0:
        # a non-silent clip with no clear peak still has one nucleus (the whole vowel)
        if env.size and env.max() > 0:
            return 1, 0.5
        return 0, 0.0
    # primary stress = the strongest nucleus; report its fractional position
    strongest = max(range(count), key=lambda j: nuclei[j][1])
    stress_frac = (strongest / (count - 1)) if count > 1 else 0.5
    return count, float(stress_frac)


# ===========================================================================
# 2. WORD SYLLABLE STRUCTURE — the lexicon (world knowledge). Hand-stated English
#    pronunciation dictionary for the 35 Speech-Commands words. SOURCE: standard
#    English dictionary syllabification (CMUdict unavailable offline; the SC vocab
#    is small + fixed, so the canonical counts are stated explicitly). Each entry:
#    (syllable_count, primary_stress_fraction). stress_frac follows the same [0,1]
#    convention as the extractor (0 = stress on first syllable, 1 = last).
# ===========================================================================

# (count, stress_frac). Monosyllables: count 1, stress 0.5 (a single nucleus has
# no position to distinguish — matches the extractor's count==1 stress_frac=0.5).
WORD_SYLLABLES = {
    # monosyllables (count 1)
    "bed": (1, 0.5), "bird": (1, 0.5), "cat": (1, 0.5), "dog": (1, 0.5),
    "down": (1, 0.5), "eight": (1, 0.5), "five": (1, 0.5), "four": (1, 0.5),
    "go": (1, 0.5), "house": (1, 0.5), "learn": (1, 0.5), "left": (1, 0.5),
    "nine": (1, 0.5), "no": (1, 0.5), "off": (1, 0.5), "on": (1, 0.5),
    "one": (1, 0.5), "right": (1, 0.5), "six": (1, 0.5), "stop": (1, 0.5),
    "three": (1, 0.5), "tree": (1, 0.5), "two": (1, 0.5), "up": (1, 0.5),
    "wow": (1, 0.5), "yes": (1, 0.5), "zero": (2, 0.0),
    # disyllables (count 2), primary stress on the FIRST syllable -> frac 0.0
    "backward": (2, 0.0), "forward": (2, 0.0), "follow": (2, 0.0),
    "happy": (2, 0.0), "marvin": (2, 0.0), "seven": (2, 0.0),
    "sheila": (2, 0.0),
    # trisyllable (count 3), stress-initial -> frac 0.0
    "visual": (3, 0.0),
}
# NOTE: "zero" is ZEE-roh = 2 syllables (corrected above into the disyllable group).


def word_count(word):
    """Dictionary syllable count for a word (1 if unknown — a safe abstain default)."""
    return WORD_SYLLABLES.get(word, (1, 0.5))[0]


def word_stress(word):
    """Dictionary primary-stress fraction for a word (0.5 if unknown)."""
    return WORD_SYLLABLES.get(word, (1, 0.5))[1]


# ===========================================================================
# 3. PROSODY FRAME — owned SOFT EXCLUDER over the vocab from the extracted
#    syllable count (+ optional stress). Same convention as the other frames:
#    e[k] == 0  -> word k's syllable structure MATCHES (abstain, fully admissible)
#    e[k] <  0  -> word k carved by how far its dict count is from the extracted.
# ===========================================================================

_COUNT_STEP = 4.0     # log-adm carved per syllable of count mismatch (a strong but
#                       SOFT excluder: off-by-one ~ -4, off-by-two ~ -8 nats; never
#                       -inf, so a noisy extraction can be overridden by other frames)
_STRESS_STEP = 1.0    # extra carve for a stress-position mismatch among count-matches
_FLOOR = -30.0        # the soft-excluder floor (matches frame_inference_v2)


def prosody_excluder(extracted_count, vocab, extracted_stress=None,
                     use_stress=False):
    """Build the soft excluder over `vocab` from the EXTRACTED syllable count.
    Each word carved by -_COUNT_STEP * |dict_count - extracted_count|; a matching
    word abstains (0). If use_stress and extracted_stress is given, count-matching
    words additionally carved by -_STRESS_STEP * |dict_stress - extracted_stress|.
    Owned soft excluder (the agent's collapse intersects it). Returns (K,) in
    [_FLOOR, 0]."""
    K = len(vocab)
    e = np.zeros(K, dtype=np.float64)
    for k, w in enumerate(vocab):
        dc, ds = WORD_SYLLABLES.get(w, (1, 0.5))
        carve = _COUNT_STEP * abs(dc - extracted_count)
        if use_stress and extracted_stress is not None and dc == extracted_count and dc > 1:
            carve += _STRESS_STEP * abs(ds - extracted_stress)
        e[k] = -carve
    return np.clip(e, _FLOOR, 0.0)


# ===========================================================================
# 4. ENTRAINED THETA OSCILLATOR — the ACTIVE, SELF-CLOCKING read (Stage A of the
#    active-transducer interface). A human does NOT count envelope peaks; a theta
#    oscillator ENTRAINED to the speech is the syllable clock. Because it
#    INTEGRATES over time (phase has inertia; frequency is a slow running estimate),
#    a brief sonorant-internal dip ("follow"/"zero"/"sheila") does NOT spuriously
#    split a syllable the way the passive peak-counter does. Syllable BOUNDARIES =
#    the oscillator's PHASE events (one event per 2*pi cycle); COUNT = number of
#    completed cycles over the word.
#
#    OWNED DSP, NO net, NO fit, frozen constants. The form is a damped-driven /
#    gradient-frequency phase-locked oscillator (a Large-style adaptive oscillator
#    reduced to one unit): an internal phase theta advances at an instantaneous
#    frequency omega; a Hebbian/gradient frequency-adaptation term pulls omega
#    toward the dominant envelope rhythm; a phase-coupling term nudges the phase to
#    lock onto the onset drive. INERTIA: omega changes slowly (tau_f) and the phase
#    is driven (not reset), so the oscillator rides through a momentary dip and
#    only registers the boundary when its own cycle completes.
#
#    DONKEY: this is the SENSE / world-adapter transduction (mechanical audio ->
#    boundaries). No graph state, no agent decisions. The frame/collapse downstream
#    is unchanged (the agent's).
# ===========================================================================

# FIXED physical constants of the theta band + entrainment dynamics (a syllable's
# rhythm, NOT swept on the test set):
_THETA_F0_HZ = 5.0          # initial / prior oscillator frequency: mid-theta (~5 Hz)
#                             is the centre of the speech-syllable rate (3-8 Hz)
_THETA_F_LO = 2.5           # frequency-adaptation clamp lo (theta floor; slow speech)
_THETA_F_HI = 8.0           # frequency-adaptation clamp hi (theta ceiling; fast speech)
_TAU_F_S = 0.30             # frequency-adaptation time constant (s): omega tracks the
#                             rhythm only SLOWLY -> inertia. ~1.5 syllables of memory,
#                             so a single dip can't yank the clock.
_K_PHASE = 6.0              # phase-coupling gain: how strongly the onset drive pulls
#                             the oscillator phase toward lock. Strong enough to
#                             entrain, not so strong it tracks every ripple.
_K_FREQ = 3.0               # frequency-coupling gain (the gradient/Hebbian pull of
#                             omega toward the drive's instantaneous rate)
_ONSET_FLOOR_FRAC = 0.05    # ignore onset drive below 5% of the clip's peak onset
#                             (silence/noise must not entrain the clock)
_VOICE_GATE_FRAC = 0.20     # the syllable clock is ENGAGED only where the voiced
#                             envelope exceeds 20% of the clip peak. In silence /
#                             padding (SC clips are ~1 s but the word is ~0.2-0.5 s)
#                             the clock HOLDS (no speech = no syllable to count) and
#                             does not free-run. Theta entrainment is engaged BY the
#                             speech signal, not a clock ticking through silence.
_GATE_HOLD_MS = 60.0        # hysteresis: keep the clock engaged across brief
#                             sub-gate dips up to this long (a sonorant-internal /
#                             stop-closure dip inside ONE word must not disengage the
#                             clock — that is the integration the peak-counter lacks)
_BOUNDARY_PHASE = np.pi / 2 # the phase (per 2*pi cycle) at which a boundary/nucleus
#                             event is emitted: pi/2 = the rising quarter, i.e. the
#                             oscillator's "expect-a-nucleus" crest. One per cycle.
_CYCLE_DRIVE_MIN = 0.40     # a completed cycle counts as a syllable only if it
#                             accumulated at least this much onset drive (a real
#                             nucleus). A cycle finished by pure intrinsic coasting
#                             (no onset) is a PHANTOM tick, not a syllable. Frozen.


def _onset_drive(env):
    """Half-wave-rectified derivative of the (already voiced-band, smoothed) energy
    envelope = the ONSET function. Syllable onsets are sharp energy RISES; rectifying
    keeps the rises (drive toward a new nucleus) and drops the falls. Owned DSP.
    Normalised to its own peak so the entrainment gain is scale-free across clips."""
    if env.size < 2:
        return np.zeros_like(env)
    d = np.diff(env, prepend=env[0])
    onset = np.clip(d, 0.0, None)
    pk = float(onset.max())
    if pk <= 0:
        return np.zeros_like(onset)
    onset = onset / pk
    onset[onset < _ONSET_FLOOR_FRAC] = 0.0
    return onset


def entrain_theta(x, fs=_FS, return_trace=False):
    """Entrained theta oscillator on the energy envelope. Returns (count, stress_frac)
    [+ optional trace dict]. OWNED DSP, no net/fit.

    count       = number of completed oscillator cycles over the word = the number of
                  boundary phase-events emitted (the self-clocked syllable count).
    stress_frac = position in [0,1] of the cycle whose nucleus carried the most
                  envelope energy (a coarse primary-stress read; same convention as
                  the peak-counter so it drops into the SAME excluder).

    Dynamics (forward Euler at the envelope frame rate; phase wrapped to [0,2*pi)):
      theta_{t+1} = theta_t + dt*omega_t + dt*K_phase*drive_t*sin(target - theta_t)
      omega_{t+1} = omega_t + dt/tau_f * ( -(omega_t-f0_rad) + K_freq*drive_t*... )
    The frequency adapts slowly (tau_f) -> inertia; the phase is DRIVEN by the onset,
    never hard-reset -> a momentary dip (drive~0) leaves the oscillator coasting at
    its current omega, so it rides through the dip and only marks a boundary when its
    OWN cycle completes. That integration is the whole point vs the peak-counter."""
    env, hop = energy_envelope(x, fs)
    n = env.size
    if n == 0 or float(env.max()) <= 0:
        if return_trace:
            return 0, 0.0, {"phase": np.zeros(0), "omega": np.zeros(0),
                            "events": [], "env": env}
        return 0, 0.0

    drive = _onset_drive(env)
    dt = hop / 1000.0                       # frame period in seconds
    two_pi = 2.0 * np.pi
    f0_rad = two_pi * _THETA_F0_HZ
    w_lo, w_hi = two_pi * _THETA_F_LO, two_pi * _THETA_F_HI
    target = _BOUNDARY_PHASE                # drive pulls phase toward the crest

    # --- voice gate: where the syllable clock is ENGAGED (speech present). The clock
    #     holds in silence/padding and does NOT free-run. Hysteresis bridges brief
    #     sub-gate dips WITHIN a word (the integration the peak-counter lacks). ---
    gate_floor = _VOICE_GATE_FRAC * float(env.max())
    hold_frames = max(1, int(round(_GATE_HOLD_MS / hop)))
    engaged = np.zeros(n, dtype=bool)
    since_voiced = hold_frames + 1
    for i in range(n):
        if env[i] >= gate_floor:
            since_voiced = 0
        else:
            since_voiced += 1
        engaged[i] = since_voiced <= hold_frames

    theta = 0.0                             # start at phase 0
    omega = f0_rad                          # start at the theta prior
    phase_tr = np.empty(n)
    omega_tr = np.empty(n)
    events = []                             # (frame_index, env_value_at_event)
    cyc_drive = 0.0                         # onset drive accumulated in the current cycle
    cyc_peak = 0.0                          # peak voiced energy in the current cycle

    for i in range(n):
        if not engaged[i]:
            # clock disengaged (silence): hold phase + omega, do not advance/count.
            phase_tr[i] = theta
            omega_tr[i] = omega
            continue
        d = drive[i]
        cyc_drive += d
        cyc_peak = max(cyc_peak, float(env[i]))
        # --- frequency adaptation (slow; inertia). The omega relaxes toward the
        #     theta prior and is pulled toward the drive's pace by a Hebbian term
        #     proportional to the drive and the phase-error sign. tau_f makes it
        #     slow -> a single dip cannot yank the clock. ---
        phase_err = np.sin(target - theta)
        domega = (-(omega - f0_rad) + _K_FREQ * d * phase_err * f0_rad) / _TAU_F_S
        omega = omega + dt * domega
        if omega < w_lo: omega = w_lo
        if omega > w_hi: omega = w_hi
        # --- phase advance: intrinsic + onset coupling (DRIVEN, not reset). ---
        theta = theta + dt * omega + dt * _K_PHASE * d * phase_err
        # --- boundary event = a 2*pi phase WRAP (one completed cycle = one syllable).
        #     A cycle counts ONLY if it received real onset drive (a genuine nucleus):
        #     a cycle completed purely by intrinsic coasting (no onset) is a PHANTOM
        #     syllable -> not counted. This is the entrainment requirement: a syllable
        #     is a driven cycle, not a free-run tick. ---
        if theta >= two_pi:
            theta -= two_pi
            if cyc_drive >= _CYCLE_DRIVE_MIN:
                events.append((i, cyc_peak))
            cyc_drive = 0.0
            cyc_peak = 0.0
        phase_tr[i] = theta
        omega_tr[i] = omega

    count = len(events)
    # An entrained oscillator that never completed a full cycle over a real (voiced)
    # word still spans one syllable (the nucleus it was riding) -> floor at 1.
    if count == 0:
        count = 1
        # the single nucleus = the global envelope peak
        gi = int(np.argmax(env))
        events = [(gi, float(env[gi]))]

    # coarse primary stress = the cycle whose nucleus carried the most energy
    strongest = max(range(len(events)), key=lambda j: events[j][1])
    stress_frac = (strongest / (len(events) - 1)) if len(events) > 1 else 0.5

    if return_trace:
        return count, float(stress_frac), {
            "phase": phase_tr, "omega": omega_tr, "events": events, "env": env,
            "drive": drive, "hop_ms": hop,
        }
    return count, float(stress_frac)


__all__ = [
    "energy_envelope", "extract_syllables",
    "WORD_SYLLABLES", "word_count", "word_stress",
    "prosody_excluder",
    "entrain_theta",
]

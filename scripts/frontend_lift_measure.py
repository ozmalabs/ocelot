"""frontend_lift_measure — the DECISIVE test, isolated.

Does giving the agent direct front-end control LIFT the FSDD speaker-invariance
plateau? Measure the SpeechWorld's held-out FSDD digit cookie-rate as the agent
WIDENS its graph-resident front end, one cue at a time, exactly as the plateau Rule
would drive it (modify_frontend's graph Argmax order). This isolates the front-end
effect from the timing of the live loop.

PROTOCOL (LOSO-style, the honest held-out): bank a fixed set of FSDD exemplars
(train speakers), measure the held-out cookie-rate on a DISJOINT set of FSDD probes
(held speakers — real speaker invariance). Then call the agent's modify_frontend
(the graph decision adds the next cue), RE-BANK at the new width, re-measure. The
front-end width climbs by the agent's OWN graph-resident choice; we read the curve.

NO-DONKEY: every cue is composable DSP the agent owns; the recognizer is the
many-settings Argmax-of-product in feature space; Piper/espeak never enter (this is
real FSDD human speech). The modification SET + ORDER are the graph's, not ours.

Run: python -m scripts.frontend_lift_measure [n_per_speaker_per_digit]
"""
from __future__ import annotations

import sys

import numpy as np

import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from substrate_rs import Substrate


CELL = "digit|fsdd|en"


def _load_fsdd_by_speaker(n_per):
    """{speaker: [(word, x, fs)]} from the real-human FSDD recordings."""
    import os, re
    fn_re = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
    digits = W._DIGIT_WORDS["en"]
    by_spk = {}
    counts = {}
    for fn in sorted(os.listdir(W._FSDD_DIR)):
        m = fn_re.match(fn)
        if not m:
            continue
        word = digits[int(m.group(1))]
        spk = m.group(2)
        key = (spk, word)
        if counts.get(key, 0) >= n_per:
            continue
        counts[key] = counts.get(key, 0) + 1
        x, fs = W.load_fsdd_clip(os.path.join(W._FSDD_DIR, fn))
        by_spk.setdefault(spk, []).append((word, x, fs))
    return by_spk


def _rebank(s, train_items):
    """Wipe + re-bank the cell's exemplars at the CURRENT front-end width (so the
    bank carries every active cue). Mechanical world-I/O."""
    # remove existing exemplars for the cell
    for c in list(s.nodes("Concept")):
        a = s.node(c)["attrs"]
        if a.get("origin") == "speech_world" and a.get("cell_key") == CELL:
            for ex in list(s.neighbours(c, "has_exemplar")):
                try:
                    s.remove_node(ex)
                except Exception:
                    pass
    for (w, x, fs) in train_items:
        W.bank_exemplar(s, w, CELL, x, fs)


def _measure(s, probes):
    correct = 0
    for (w, x, fs) in probes:
        ch = W.feature_channels(s, x, fs)
        g = W.blind_guess(s, ch, CELL)
        correct += int(g == w)
    return correct / max(len(probes), 1)


def run(n_per=6):
    by_spk = _load_fsdd_by_speaker(n_per)
    speakers = sorted(by_spk)
    print(f"FSDD: {len(speakers)} speakers {speakers}, "
          f"{sum(len(v) for v in by_spk.values())} recordings", flush=True)

    # how many front-end widenings the repertoire allows
    max_mods = len(FE.REPERTOIRE_CUES)

    # LOSO: each speaker held out once; mean held-out cookie-rate per front-end width.
    width_curve = {}     # width_label -> list of per-fold held-out rates
    width_labels = []
    for held in speakers:
        s = Substrate()
        W.install_speech_world_rules(s)
        W.install_cell(s, "digit", "fsdd", "en")
        train = [it for spk in speakers if spk != held for it in by_spk[spk]]
        probes = by_spk[held]

        labels_this_fold = []
        # width 0 = the seed front end (3 cues)
        _rebank(s, train)
        r = _measure(s, probes)
        lab = f"{FE.n_active(s)}cues(seed)"
        labels_this_fold.append(lab)
        width_curve.setdefault(lab, []).append(r)

        for k in range(max_mods):
            mod = FE.modify_frontend(s)        # the AGENT's graph choice adds a cue
            if mod is None:
                break
            _rebank(s, train)                  # re-bank at the new width
            r = _measure(s, probes)
            lab = f"{FE.n_active(s)}cues(+{mod['name']})"
            labels_this_fold.append(lab)
            width_curve.setdefault(lab, []).append(r)
        if not width_labels:
            width_labels = labels_this_fold
        print(f"  held {held}: " + "  ".join(
            f"{lab.split('(')[0]}={width_curve[lab][-1]:.3f}"
            for lab in labels_this_fold), flush=True)

    print("\n" + "=" * 64, flush=True)
    print("FSDD held-out cookie-rate vs the agent's self-widened front end "
          "(LOSO mean)", flush=True)
    print("=" * 64, flush=True)
    means = []
    for lab in width_labels:
        m = float(np.mean(width_curve[lab]))
        means.append(m)
        print(f"  {lab:34s} {m:.3f}", flush=True)
    seed_m = means[0]
    best_m = max(means)
    best_lab = width_labels[int(np.argmax(means))]
    print("-" * 64, flush=True)
    print(f"  seed front end (3 cues):  {seed_m:.3f}", flush=True)
    print(f"  best self-widened:        {best_m:.3f}  at {best_lab}", flush=True)
    print(f"  LIFT: {best_m - seed_m:+.3f}  "
          f"(plateau band ~0.30-0.40; chance 0.100)", flush=True)
    verdict = ("LIFTS past the plateau" if best_m > 0.40 and best_m > seed_m + 0.02
               else ("widens but plateau holds" if best_m > seed_m + 0.02
                     else "no lift"))
    print(f"  VERDICT: the agent's own front-end widening {verdict}", flush=True)
    return width_labels, means


if __name__ == "__main__":
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    run(n_per)

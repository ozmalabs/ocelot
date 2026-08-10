"""many_settings_hvpt_accept — iter-33 acceptance: does the agent's combinatorial
product over MANY SETTINGS of its filters/transforms beat the SINGLE strong
setting?

THE INSIGHT (user): "there is no reason to have ONE setting for a particular filter
or transform; that's the whole point of a graph." iter-32 combined two channels and
LOST to the single strong flat channel — its residual was NODE QUALITY: each cue was
ONE SETTING (one time-frequency tradeoff), and the uncertainty principle caps any one
setting. A graph instantiates the SAME filter at MANY settings, each a node, and
combines ALL of them (the two-ears result generalised to N ears,
ozma_wall_is_self_imposed). This script wires that and tests it.

THE MANY-SETTINGS GRAPH (domains/filter_settings.py + domains/many_settings_recognizer):
  · the COCHLEAR front-end at MANY time-frequency tradeoffs (sharp-time .. sharp-freq,
    via env_cut / dur_cut / n_frames) — each setting a node;
  · for each cochlear setting, BOTH a flat (spectral-detail) readout AND the agent's
    order-1-over-time TRANSITION channel at MANY temporal windows (short/med/long)
    — each a node.
  · ALL nodes' per-candidate likelihoods are MULTIPLIED in the agent's
    recognition_graph Argmax of a variadic Times (the Bayes product, generalised
    from iter-32's 2-channel product to N channels).

THE ONE HARD RULE: COMBINE ALL settings — every instantiated setting feeds the
product. NO sweep-and-keep-best (the forbidden negative-space search), NO fit, NO
winning-setting pick, NO global hand-weight. Each setting's likelihood is
scale-normalised by its OWN median distance (read from the data). The product sorts
the settings out.

COMPARATORS (multi-metric, LOSO over 6 FSDD speakers + persona, with SHUFFLE):
  · MANY-SETTINGS GRAPH (this iter)             — N settings, all combined
  · SINGLE-SETTING FLAT (iter-31 strong channel) — the middle setting's flat readout
  · iter-32 TWO-NODE COMBO (flat·trans)         — the middle setting, two channels
  · FROZEN (the cohort-warped front-end)        — the baked-in regression baseline

Per cochlear setting the patch bank is GROWN by the cross-voice transition survival
selector (grown_representation) — the same selector, just applied per setting.

Run: python -m scripts.many_settings_hvpt_accept [n_per_speaker_per_digit] [rounds]
"""
import sys
import random

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from scripts.mine_whisper import gather, load_wav
from domains.invariant_units import canonical_log_centroid
from domains.grown_representation import (
    seed_patches, bands_to_patches, grow_representation, transition_channel,
)
from domains.filter_settings import (
    cochleagram, COCHLEAR_SETTINGS, TRANSITION_WINDOWS, transition_multiwindow,
)
from domains.invariant_units import invariant_transform
import domains.many_settings_recognizer as MS
import domains.combinatorial_recognizer as CR
from substrate_rs import Substrate


# ---------------------------------------------------------------------------
# Per-utterance vectors (same L2-normalised readouts the iter-32 harness uses).
# ---------------------------------------------------------------------------

def l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def flat_readout(R):
    return l2(R.flatten())


def trans_readout(R, patches):
    return l2(transition_channel(R, patches))


def trans_window_readout(R, patches, n_windows):
    return l2(transition_multiwindow(R, patches, n_windows))


def grown_repr(M_band, patches):
    """NO cohort warp; per-utterance mean removal + the grown patch bank."""
    mu = M_band.mean(axis=0, keepdims=True)
    return bands_to_patches(M_band - mu, patches)


def frozen_repr(M_band, canonical, patches):
    t = invariant_transform(M_band, canonical, do_vtln=True, do_cmvn=True,
                            do_context=False)
    return bands_to_patches(t, patches)


def heldout_1nn(train_vecs, train_words, test_vecs, test_words):
    Xtr = np.asarray(train_vecs)
    Xtr = Xtr / (np.linalg.norm(Xtr, axis=1, keepdims=True) + 1e-9)
    Xte = np.asarray(test_vecs)
    Xte = Xte / (np.linalg.norm(Xte, axis=1, keepdims=True) + 1e-9)
    sim = Xte @ Xtr.T
    pred = np.asarray(train_words)[sim.argmax(axis=1)]
    return float((pred == np.asarray(test_words)).mean())


def heldout_1nn_pooled(train_vecs, train_words, test_vecs, test_words):
    return heldout_1nn(train_vecs, train_words, test_vecs, test_words)


# ---------------------------------------------------------------------------
# The N-channel combinatorial recognition (the agent's Argmax-of-product Term).
# ---------------------------------------------------------------------------

_MS_SUB = None
_MS_WC: dict = {}
_MS_TERM = None
_MS_NCH = None


def _ms_substrate(candidate_words, n_channels):
    """A tiny substrate holding one Concept per candidate word (is_word) on which
    the agent's many-settings Argmax-of-product Term ranges. The per-setting
    likelihoods are written onto these nodes per query."""
    global _MS_SUB, _MS_TERM, _MS_NCH
    if _MS_SUB is None or _MS_NCH != n_channels:
        _MS_SUB = Substrate()
        _MS_TERM = MS._Pred(MS.predict_many_settings_term(n_channels))
        _MS_NCH = n_channels
        _MS_WC.clear()
    for w in candidate_words:
        if w not in _MS_WC:
            c = _MS_SUB.add_node("Concept", {"name": w})
            _MS_SUB.set_attr(c, MS.WORD_ATTR, 1.0)
            _MS_WC[w] = c
    return _MS_SUB


def heldout_many_settings(channel_train, channel_test, train_words, test_words):
    """The MANY-SETTINGS combinatorial recognition. `channel_train` /
    `channel_test` are lists (one per setting/node) of per-utterance vectors. Each
    held-out query is recognised by the agent's recognition_graph Argmax of the
    Bayes PRODUCT of ALL N settings' per-candidate likelihoods (a variadic Times,
    evaluated natively). COMBINE ALL — no setting selected, no weight, no fit."""
    n_ch = len(channel_train)
    Xs = [np.asarray(ct) for ct in channel_train]
    candidates = sorted(set(train_words))
    sub = _ms_substrate(candidates, n_ch)
    correct = 0
    n_test = len(test_words)
    for qi in range(n_test):
        for ci in range(n_ch):
            p = MS.channel_likelihood(np.asarray(channel_test[ci][qi]),
                                      Xs[ci], train_words, candidates)
            for w in candidates:
                sub.set_attr(_MS_WC[w], MS.channel_attr(ci), p[w])
        pred = sub.evaluate(_MS_TERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        correct += int(pw == test_words[qi])
    return correct / max(n_test, 1)


def heldout_two_node_combo(train_flat, train_trans, train_words,
                           test_flat, test_trans, test_words):
    """iter-32's TWO-NODE combo (flat·trans, middle setting) via the SAME N-channel
    machinery with N=2 — the apples-to-apples iter-32 comparator."""
    return heldout_many_settings([train_flat, train_trans],
                                 [test_flat, test_trans],
                                 train_words, test_words)


# ---------------------------------------------------------------------------
# Build all the per-setting channels for a set of utterances under a held-out fold.
# ---------------------------------------------------------------------------

def _grow_for_setting(voice_word_matrices, rounds):
    """Grow the patch bank for ONE cochlear setting under the cross-voice
    transition-contrast survival selector (the same selector iter-30/31/32 use)."""
    voice_band_matrices = {v: [M for (_, M) in items]
                           for v, items in voice_word_matrices.items()}
    seed = seed_patches()
    grown = grow_representation(
        voice_band_matrices, seed=seed, rounds=rounds,
        selector="transition", voice_word_matrices=voice_word_matrices)
    return grown["patches"], grown["grown"]


def build_fold(voice_audio, held_voice, rounds=2, shuffle=False):
    """One LOSO fold. `voice_audio` = {voice: [(x, fs, word), ...]} (raw audio, so
    each cochlear setting recomputes its own cochleagram). Returns a dict of channel
    lists (train + held) for: the MANY-SETTINGS graph, the single-setting flat, the
    two-node combo, and frozen — plus the train/test word labels."""
    train_voices = [v for v in voice_audio if v != held_voice]

    # Precompute, per cochlear setting, the band-matrices for every utterance.
    # setting_band[(voice)] = [(word, M_band_at_this_setting), ...]
    settings = COCHLEAR_SETTINGS
    # per-setting per-voice band matrices for train (used to GROW) + held.
    setting_train_bands = []   # list over settings of {voice: [(word, M)]}
    setting_held_bands = []    # list over settings of [(word, M)]
    for (_, env_cut, dur_cut, nf) in settings:
        tr = {}
        for v in train_voices:
            tr[v] = [(w, cochleagram(x, fs, env_cut, dur_cut, nf))
                     for (x, fs, w) in voice_audio[v]]
        held = [(w, cochleagram(x, fs, env_cut, dur_cut, nf))
                for (x, fs, w) in voice_audio[held_voice]]
        setting_train_bands.append(tr)
        setting_held_bands.append(held)

    # SHUFFLE control: randomise the voice partition (words stay attached), so the
    # cross-voice survival selector sees no real voice structure. Applied to each
    # setting's training partition identically (same shuffle order across settings).
    if shuffle:
        rng = random.Random(1234)
        k = len(train_voices)
        # one shuffle order over the (voice,idx) slots, reused per setting.
        slot_order = None
        new_setting_train = []
        for tr in setting_train_bands:
            flat = [(w, M) for v in train_voices for (w, M) in tr[v]]
            if slot_order is None:
                slot_order = list(range(len(flat)))
                rng.shuffle(slot_order)
            flat = [flat[i] for i in slot_order]
            shuf = {f"shuf{i}": [] for i in range(k)}
            for idx, (w, M) in enumerate(flat):
                shuf[f"shuf{idx % k}"].append((w, M))
            new_setting_train.append(shuf)
        setting_train_bands = new_setting_train
        train_voices = [f"shuf{i}" for i in range(k)]

    # Grow a patch bank per cochlear setting (selector decides; no sweep).
    setting_patches = []
    grown_counts = []
    for tr in setting_train_bands:
        patches, grown = _grow_for_setting(tr, rounds)
        setting_patches.append(patches)
        grown_counts.append(len(grown))

    # Build the channel readouts. For each cochlear setting: a FLAT channel plus a
    # TRANSITION channel per temporal window. Each is a node feeding the product.
    many_train, many_held, many_names = [], [], []
    train_words, held_words = None, None
    middle_idx = next(i for i, s in enumerate(settings) if s[0] == "middle")
    single_flat_train = single_flat_held = None
    combo_flat_train = combo_flat_held = None
    combo_trans_train = combo_trans_held = None

    for si, (sname, *_rest) in enumerate(settings):
        patches = setting_patches[si]
        tr = setting_train_bands[si]
        held = setting_held_bands[si]
        # train readouts (flat + each transition window)
        tr_items = [(w, M) for v in train_voices for (w, M) in tr[v]]
        tr_words = [w for (w, _) in tr_items]
        he_words = [w for (w, _) in held]
        if train_words is None:
            train_words, held_words = tr_words, he_words
        # FLAT channel for this setting.
        tr_flat = [flat_readout(grown_repr(M, patches)) for (_, M) in tr_items]
        he_flat = [flat_readout(grown_repr(M, patches)) for (_, M) in held]
        many_train.append(tr_flat); many_held.append(he_flat)
        many_names.append(f"{sname}:flat")
        # TRANSITION channels at each temporal window for this setting.
        for (wname, nwin) in TRANSITION_WINDOWS:
            tr_t = [trans_window_readout(grown_repr(M, patches), patches, nwin)
                    for (_, M) in tr_items]
            he_t = [trans_window_readout(grown_repr(M, patches), patches, nwin)
                    for (_, M) in held]
            many_train.append(tr_t); many_held.append(he_t)
            many_names.append(f"{sname}:{wname}")
        # Capture the MIDDLE setting's flat + (w2) trans as the single-setting and
        # iter-32 two-node comparators.
        if si == middle_idx:
            single_flat_train, single_flat_held = tr_flat, he_flat
            combo_flat_train, combo_flat_held = tr_flat, he_flat
            combo_trans_train = [trans_readout(grown_repr(M, patches), patches)
                                 for (_, M) in tr_items]
            combo_trans_held = [trans_readout(grown_repr(M, patches), patches)
                                for (_, M) in held]

    # FROZEN comparator (cohort-warped front-end, fixed seed bank, middle setting's
    # band matrices). Built on the middle setting's bands (the agent's existing
    # baked-in tradeoff).
    seed = seed_patches()
    mtr = setting_train_bands[middle_idx]
    mheld = setting_held_bands[middle_idx]
    tr_items_m = [(w, M) for v in train_voices for (w, M) in mtr[v]]
    canonical = canonical_log_centroid([M for (_, M) in tr_items_m])
    frozen_train = [flat_readout(frozen_repr(M, canonical, seed))
                    for (_, M) in tr_items_m]
    frozen_held = [flat_readout(frozen_repr(M, canonical, seed))
                   for (_, M) in mheld]

    return {
        "many_train": many_train, "many_held": many_held, "many_names": many_names,
        "single_flat_train": single_flat_train, "single_flat_held": single_flat_held,
        "combo_flat_train": combo_flat_train, "combo_flat_held": combo_flat_held,
        "combo_trans_train": combo_trans_train, "combo_trans_held": combo_trans_held,
        "frozen_train": frozen_train, "frozen_held": frozen_held,
        "train_words": train_words, "held_words": held_words,
        "n_channels": len(many_train), "grown_counts": grown_counts,
        "held_voice": held_voice, "shuffle": shuffle,
        "n_held": len(held_words), "n_train": len(train_words),
    }


def score_fold(f):
    """Compute all metrics for one built fold."""
    tw, hw = f["train_words"], f["held_words"]
    many = heldout_many_settings(f["many_train"], f["many_held"], tw, hw)
    single_flat = heldout_1nn(f["single_flat_train"], tw, f["single_flat_held"], hw)
    combo2 = heldout_two_node_combo(f["combo_flat_train"], f["combo_trans_train"],
                                    tw, f["combo_flat_held"], f["combo_trans_held"],
                                    hw)
    frozen = heldout_1nn(f["frozen_train"], tw, f["frozen_held"], hw)
    return {"held_voice": f["held_voice"], "shuffle": f["shuffle"],
            "n_channels": f["n_channels"], "grown_counts": f["grown_counts"],
            "many": many, "single_flat": single_flat, "combo2": combo2,
            "frozen": frozen, "n_held": f["n_held"], "n_train": f["n_train"],
            "many_names": f["many_names"]}


def _report_fold(r):
    print(f"\n--- held-out {r['held_voice']}"
          f"{' [SHUFFLE]' if r['shuffle'] else ''} ---")
    print(f"  channels (settings) combined: {r['n_channels']}  "
          f"(grown patch counts per cochlear setting: {r['grown_counts']})")
    print(f"  held utterances {r['n_held']}  train utterances {r['n_train']}")
    print(f"  MANY-SETTINGS graph {r['many']:.3f}   "
          f"single-setting flat {r['single_flat']:.3f}   "
          f"iter-32 2-node combo {r['combo2']:.3f}   "
          f"frozen {r['frozen']:.3f}")
    print(f"     Δ(many - single-flat) {r['many'] - r['single_flat']:+.3f}   "
          f"Δ(many - combo2) {r['many'] - r['combo2']:+.3f}   "
          f"Δ(many - frozen) {r['many'] - r['frozen']:+.3f}")


# ---------------------------------------------------------------------------
# REAL-SPEAKER HVPT (LOSO over 6 FSDD speakers).
# ---------------------------------------------------------------------------

def real_speaker_hvpt(n_per, rounds=2):
    items = gather(n_per_class_per_speaker=n_per)
    voice_audio: dict = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers")
    print(f"speakers (voices): {speakers}")
    print(f"cochlear settings: {[s[0] for s in COCHLEAR_SETTINGS]}")
    print(f"transition windows: {[w[0] for w in TRANSITION_WINDOWS]}")
    print(f"=> channels per fold = {len(COCHLEAR_SETTINGS)} settings x "
          f"(1 flat + {len(TRANSITION_WINDOWS)} trans) = "
          f"{len(COCHLEAR_SETTINGS) * (1 + len(TRANSITION_WINDOWS))}")

    real, shuf = [], []
    for held in speakers:
        f = build_fold(voice_audio, held, rounds=rounds, shuffle=False)
        r = score_fold(f)
        _report_fold(r)
        real.append(r)
        sf = build_fold(voice_audio, held, rounds=rounds, shuffle=True)
        sr = score_fold(sf)
        _report_fold(sr)
        shuf.append(sr)
    return real, shuf


# ---------------------------------------------------------------------------
# PERSONA HVPT (agent-generated voices, held-out persona).
# ---------------------------------------------------------------------------

def _repitch_retract(x, fs, vtl):
    if vtl == 1.0 or x.size == 0:
        return x
    n = max(1, int(round(x.size / vtl)))
    idx = np.clip((np.arange(n) * vtl).astype(int), 0, x.size - 1)
    return np.ascontiguousarray(x[idx])


def persona_hvpt(n_per, rounds=2):
    from domains.persona_speech_world import DEFAULT_PERSONAS
    held_persona = ("quinn", 150.0, 4.5, 1.25)
    personas = list(DEFAULT_PERSONAS) + [held_persona]
    items = gather(n_per_class_per_speaker=n_per)
    src_spk = "george"
    base = [(load_wav(p)[0], load_wav(p)[1], str(d))
            for p, d, s in items if s == src_spk]
    print(f"\nPERSONA source: {src_spk}, {len(base)} base recordings; "
          f"personas {[p[0] for p in personas]} (held-out {held_persona[0]})")
    voice_audio: dict = {}
    for name, f0, q, vtl in personas:
        for x, fs, word in base:
            voice_audio.setdefault(name, []).append(
                (_repitch_retract(x, fs, vtl), fs, word))
    f = build_fold(voice_audio, held_persona[0], rounds=rounds, shuffle=False)
    r = score_fold(f)
    _report_fold(r)
    sf = build_fold(voice_audio, held_persona[0], rounds=rounds, shuffle=True)
    sr = score_fold(sf)
    _report_fold(sr)
    return r, sr


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print("=" * 72)
    print("ITER-33 MANY-SETTINGS GRAPH HVPT — N settings per filter, all combined")
    print("=" * 72)

    real, shuf = real_speaker_hvpt(n_per, rounds=rounds)
    persona, persona_shuf = persona_hvpt(n_per, rounds=rounds)

    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    print("\n" + "=" * 72)
    print("VERDICT (mean over held-out voices)")
    print("=" * 72)

    gm = mean(real, "many"); gsf = mean(real, "single_flat")
    gc2 = mean(real, "combo2"); gfr = mean(real, "frozen")
    sm = mean(shuf, "many"); ssf = mean(shuf, "single_flat")
    sc2 = mean(shuf, "combo2")
    print("\nREAL-SPEAKER HVPT (LOSO over 6 FSDD speakers):")
    print(f"  channels combined per fold: {real[0]['n_channels']}")
    print(f"  MANY-SETTINGS graph   {gm:.3f}")
    print(f"  single-setting flat   {gsf:.3f}   (iter-31 strong channel)")
    print(f"  iter-32 2-node combo  {gc2:.3f}")
    print(f"  frozen                {gfr:.3f}")
    print(f"  *** many vs single-flat  Δ {gm - gsf:+.3f}  "
          f"=> {'BEATS' if gm > gsf else 'does NOT beat'} the single setting")
    print(f"  *** many vs 2-node combo Δ {gm - gc2:+.3f}  "
          f"=> {'beats' if gm > gc2 else 'does not beat'}")
    print(f"  *** many vs frozen       Δ {gm - gfr:+.3f}  "
          f"=> {'beats' if gm > gfr else 'does not beat'}")
    print("\n  SHUFFLE control:")
    print(f"  MANY REAL {gm:.3f}  SHUFFLE {sm:.3f}  "
          f"=> real {'>' if gm > sm else '<='} shuffle "
          f"({'CLEAN' if gm > sm else 'NOT CLEAN'})")
    print(f"  single-flat REAL {gsf:.3f}  SHUFFLE {ssf:.3f}")
    print(f"  2-node combo REAL {gc2:.3f}  SHUFFLE {sc2:.3f}")

    print("\nPERSONA HVPT (agent-generated voices, held-out persona):")
    print(f"  MANY-SETTINGS {persona['many']:.3f}  single-flat "
          f"{persona['single_flat']:.3f}  2-node combo {persona['combo2']:.3f}  "
          f"frozen {persona['frozen']:.3f}")
    print(f"  many vs single-flat Δ {persona['many'] - persona['single_flat']:+.3f}")
    print(f"  SHUFFLE: many {persona_shuf['many']:.3f}")

    print("\n(many-settings = N cochlear time-frequency tradeoffs x [flat + "
          "multi-window transition], ALL combined via the agent's Argmax-of-product;"
          " single-flat = the middle setting's flat readout alone; combine-all, "
          "NOT select-best, no fit, no weight)")


if __name__ == "__main__":
    main()

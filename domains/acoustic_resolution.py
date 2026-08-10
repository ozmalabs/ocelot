"""Acoustic resolution the agent manages ITSELF.

Discriminative feature invention (domains/discriminative_invention.py) saturates
because it only had 4 coarse acoustic dimensions (low/mid/high_band_mean, f0_hz).
But every AcousticSign already carries its FULL trajectory — 800 values = 32
frames x 25 cochlear/A1 patches. The 3 summary bands are just a coarse
aggregation of it. So the agent is not truly resolution-limited; it just wasn't
USING the finer data.

This makes the resolution a thing the agent KNOWS about and FIXES itself: it
summarises the trajectory into N frequency bands (N on a graph node it controls),
and when discriminative invention SATURATES (no new hypotheses several cycles)
while recognition is still poor, it recognises the resolution as the bottleneck
and DOUBLES N — exposing finer bands the next round of invention can split on.

Bands are stored as `band<N>_<i>` attrs on each sign (so predicate Term-trees can
read them) for every resolution in the ladder up to the current one, so features
invented at a coarser resolution keep working. See
[[ozma_invention_management_graph_resident]] / [[ozma_phonology_microtheory]].
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from substrate_rs import (Attr, Lit, Var, Lt, Lte, Gte, Eq, And,
                          IfThenElse, Plus, Nth)

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "acoustic_resolution.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


# Dials come from the seed JSON, not Python literals (loaded once at import).
_CFG = _load_seed()["resolution_root"]
_DEFAULT_RES = _CFG["resolution"]
_MAX_RES = _CFG["max_resolution"]      # finest resolution (A1 patch count)
_LADDER = list(_CFG["ladder"])         # the step sequence the agent climbs
_TRAJ_LEN = 800        # 32 frames x 25 patches — fixed trajectory shape
_N_PATCHES = 25


def _root(substrate):
    for n in substrate.nodes("AcousticResolutionRoot"):
        return n
    # Scalar step attrs derived from the seeded ladder (the rule reads these;
    # values come from the seed list, not hardcoded — Nth can't index in a rule).
    _lad = list(_CFG["ladder"])
    steps = {f"res_l{i}": _lad[i] for i in range(1, len(_lad))}
    return substrate.add_node("AcousticResolutionRoot", {
        "origin": "acoustic_resolution",
        "saturation_cycles": 0,                # runtime state
        "description": ("How finely the agent resolves the cochlear trajectory "
                        "into frequency bands for discrimination. The agent "
                        "raises this itself when discriminative invention "
                        "saturates while confusions persist."),
        # Seeded dials (seeds/acoustic_resolution.json): resolution, ladder,
        # max_resolution, trickle, saturate_after, poor_recognition_frac.
        **_CFG,
        **steps,
    })


def get_resolution(substrate) -> int:
    return int(substrate.node(_root(substrate))["attrs"].get(
        "resolution", _DEFAULT_RES))


def _ladder_upto(res: int):
    return [n for n in _LADDER if n <= res] or [_DEFAULT_RES]


def band_names(res: int) -> list:
    """The band attr names active at this resolution (whole ladder up to it)."""
    names = []
    for n in _ladder_upto(res):
        names += [f"band{n}_{i}" for i in range(n)]
    return names


def _patch_energies(traj) -> np.ndarray | None:
    if traj is None:
        return None
    arr = np.asarray(traj, dtype=float)
    if arr.size != _TRAJ_LEN:
        return None
    return arr.reshape(-1, _N_PATCHES).mean(axis=0)   # 25 freq-ordered energies


# Fixed-point scale for the persisted `band<N>_<i>` energy attrs (see
# PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md c1-12): these are means of a
# bounded-precision digitized signal -- their real information content is far
# below the ~52 bits of a Python float's mantissa, so multiplying by a large
# power of two and rounding to the nearest integer discards nothing a
# downstream consumer can observe (order comparisons -- formant_features's
# peak detector -- and the RATIO-based Fisher-style tests --
# discriminative_invention, cue_assessment -- are both invariant under any
# common positive rescaling), while the persisted attr becomes an exact Int
# instead of an unbounded-precision Float. 2**32 gives ~4.3e9 subdivisions per
# unit of energy -- vastly finer than the ~16-bit precision of the digitized
# audio this is a mean of -- while staying far inside i64 range for any
# realistic (even unnormalised) energy magnitude.
_BAND_FIXED_POINT_SCALE = 1 << 32


def _band_fixed_point(v: float) -> int:
    """Exact/integer-scaled fixed-point representation of a band-energy mean:
    `round(v * _BAND_FIXED_POINT_SCALE)`. Per the frame invariant (CLAUDE.md,
    2026-07-08: in-frame is integer), this is what gets persisted on the
    graph -- never the raw Float."""
    return int(round(float(v) * _BAND_FIXED_POINT_SCALE))


def enrich_sign_bands(substrate, resolution: int | None = None,
                      signs=None) -> int:
    """Compute + store `band<N>_<i>` attrs on signs (default: every AcousticSign)
    from each sign's trajectory, for each N in the ladder up to `resolution`.
    Observation enrichment (mechanical: trajectory -> finer band summaries) so
    predicate Term-trees + discrimination can read finer dimensions. Persisted
    as fixed-point Ints (`_band_fixed_point`), never raw Floats -- see
    PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md (c1-12). Returns count."""
    res = resolution if resolution is not None else get_resolution(substrate)
    ladder = _ladder_upto(res)
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    # The agent's own decision (a graph flag it sets when it implements its
    # speaker_normalization hypothesis): factor out the per-sign baseline so the
    # band features are RELATIVE (speaker/loudness invariant) instead of absolute.
    normalize = _normalize_on(substrate)
    enriched = 0
    for sign in targets:
        patches = _patch_energies(substrate.node(sign)["attrs"].get("trajectory"))
        if patches is None:
            continue
        for n in ladder:
            vals = [float(g.mean()) for g in np.array_split(patches, n)]
            if normalize and len(vals) > 1:
                m = sum(vals) / len(vals)
                vals = [v - m for v in vals]      # remove the per-sign baseline
            for i, v in enumerate(vals):
                substrate.set_attr(sign, f"band{n}_{i}", _band_fixed_point(v))
        enriched += 1
    return enriched


def enrich_sign_windows(substrate, resolution: int | None = None,
                        signs=None) -> int:
    """Observation enrichment (mechanical, the same role as enrich_sign_bands but
    split in TIME): store each band's mean energy in an EARLY and a LATE window of
    the trajectory — `band<N>_<i>_e` / `band<N>_<i>_l`. This ONLY supplies the
    temporal samples (the flat 800-value trajectory can't be indexed inside the
    DSL); the agent COMPOSES the movement FEATURE over them as a graph Term-tree in
    dynamics_features. No Python computes the dynamics — it computes the samples."""
    res = resolution if resolution is not None else get_resolution(substrate)
    ladder = _ladder_upto(res)
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    normalize = _normalize_on(substrate)
    enriched = 0
    for sign in targets:
        traj = substrate.node(sign)["attrs"].get("trajectory")
        if traj is None:
            continue
        arr = np.asarray(traj, dtype=float)
        if arr.size != _TRAJ_LEN:
            continue
        frames = arr.reshape(-1, _N_PATCHES)               # (frames, patches)
        h = max(1, frames.shape[0] // 2)
        for tag, win in (("e", frames[:h]), ("l", frames[h:])):
            patches = win.mean(axis=0)                      # 25 freq-ordered energies
            for n in ladder:
                vals = [float(g.mean()) for g in np.array_split(patches, n)]
                if normalize and len(vals) > 1:
                    m = sum(vals) / len(vals)
                    vals = [v - m for v in vals]
                for i, v in enumerate(vals):
                    substrate.set_attr(sign, f"band{n}_{i}_{tag}", v)
        enriched += 1
    return enriched


# --- the frequency-sharp SECOND EAR -------------------------------------
# The gammatone trajectory is log-spaced (sharp in time, blurry in
# frequency). Each sign also carries an `fft_trajectory`: a fixed-shape
# LINEAR-bin STFT magnitude view (fft_n_frames x fft_n_bins, covering
# 0..fft_sample_rate/2 Hz) computed in Rust at lexical-access time. Linear
# bins resolve formant peaks the gammatone blurs. We summarise the raw
# `fft_n_bins` (e.g. 128) into `fft_resolution` (e.g. 32) contiguous bands
# whose centre Hz is recoverable: band j of R spans bins
# [j*B/R, (j+1)*B/R) → Hz [j*nyq/R, (j+1)*nyq/R); centre ≈ (j+0.5)*nyq/R.

_FFT_RESOLUTION = 32     # sharp linear bands summarising the raw FFT bins


def fft_band_centre_hz(j: int, n_bands: int, sample_rate: float) -> float:
    """Centre frequency (Hz) of sharp FFT band j of n_bands. Bands are
    contiguous linear slices of 0..sample_rate/2."""
    nyq = sample_rate / 2.0
    return (j + 0.5) * nyq / float(n_bands)


def _fft_frames(substrate, sign):
    """(frames, n_bins) float array of a sign's fft_trajectory, or None."""
    a = substrate.node(sign)["attrs"]
    ft = a.get("fft_trajectory")
    if ft is None:
        return None
    n_frames = int(a.get("fft_n_frames", 0) or 0)
    n_bins = int(a.get("fft_n_bins", 0) or 0)
    arr = np.asarray(ft, dtype=float)
    if n_frames <= 0 or n_bins <= 0 or arr.size != n_frames * n_bins:
        return None
    return arr.reshape(n_frames, n_bins)


def enrich_sign_fft(substrate, resolution: int | None = None,
                    signs=None) -> int:
    """Observation enrichment from the SECOND (frequency-sharp) ear: read
    each sign's `fft_trajectory` (linear STFT magnitude, fft_n_frames x
    fft_n_bins over 0..fft_sample_rate/2) and write sharp linear bands:

      * `fft<R>_<j>`      — band j energy averaged over ALL frames
      * `fft<R>_<j>_e`    — early window (first half of frames)
      * `fft<R>_<j>_l`    — late window (second half of frames)

    with R = `resolution` (default 32) contiguous bins summarising the raw
    fft bins. Band j's centre Hz is recoverable via fft_band_centre_hz(j,R,
    sample_rate). Mirrors enrich_sign_bands/enrich_sign_windows but on the
    linear-frequency ear so the agent can compose formant cues. Returns the
    count of signs enriched. (Signs minted before the FFT ear was wired —
    no fft_trajectory — are skipped.)"""
    R = int(resolution) if resolution is not None else _FFT_RESOLUTION
    if R <= 0:
        R = _FFT_RESOLUTION
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    enriched = 0
    for sign in targets:
        frames = _fft_frames(substrate, sign)
        if frames is None:
            continue
        nf = frames.shape[0]
        h = max(1, nf // 2)
        windows = (("", frames), ("_e", frames[:h]), ("_l", frames[h:]))
        for tag, win in windows:
            if win.shape[0] == 0:
                continue
            bins = win.mean(axis=0)                       # n_bins energies
            vals = [float(g.mean()) for g in np.array_split(bins, R)]
            for j, v in enumerate(vals):
                substrate.set_attr(sign, f"fft{R}_{j}{tag}", v)
        enriched += 1
    return enriched


def fft_resolution() -> int:
    """The default sharp-FFT band resolution (R in fft<R>_<j>)."""
    return _FFT_RESOLUTION


def _normalize_on(substrate) -> bool:
    """Read the agent's normalization decision (a graph flag). Default off."""
    for n in substrate.nodes("NormalizationRoot"):
        return bool(substrate.node(n)["attrs"].get("enabled", 0))
    return False


def set_normalization(substrate, enabled: bool) -> None:
    """The agent implements (or reverts) its normalization hypothesis by setting
    the graph flag enrich_sign_bands reads."""
    root = next((n for n in substrate.nodes("NormalizationRoot")), None)
    if root is None:
        root = substrate.add_node("NormalizationRoot",
                                  {"origin": "speech_reasoning"})
    substrate.set_attr(root, "enabled", 1 if enabled else 0)


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


def _resolution_rule_terms():
    """The agent's resolution-management DECISION as Term-trees over its
    AcousticResolutionRoot's own observations AND its seeded dials (trickle,
    saturate_after, max_resolution, poor_recognition_frac, ladder) — all read
    from the root, no Python constants. Returns (sat_next, res_next)."""
    R = Var("R")
    dhyp = Attr(R, "dhyp_recent")          # new discriminative hyps last cycle
    rec = Attr(R, "recognition_frac")      # current recognition fraction
    res = Attr(R, "resolution")
    sat = Attr(R, "saturation_cycles")

    drying = And(items=(Lte(a=dhyp, b=Attr(R, "trickle")),
                        Lt(a=rec, b=Attr(R, "poor_recognition_frac"))))
    sat_next = IfThenElse(drying, Plus(items=(sat, Lit(1))), Lit(0))
    bump = And(items=(Gte(a=sat_next, b=Attr(R, "saturate_after")),
                      Lt(a=res, b=Attr(R, "max_resolution"))))
    # Step UP to the next ladder value strictly greater (seeded res_l1/2/3).
    res_up = IfThenElse(Lt(a=res, b=Attr(R, "res_l1")), Attr(R, "res_l1"),
              IfThenElse(Lt(a=res, b=Attr(R, "res_l2")), Attr(R, "res_l2"),
                         Attr(R, "res_l3")))
    res_next = IfThenElse(bump, res_up, res)
    sat_after = IfThenElse(bump, Lit(0), sat_next)
    return sat_after, res_next


def install_resolution_management_rule(substrate) -> dict:
    """Install the agent's resolution-management as a GRAPH-RESIDENT Rule on the
    AcousticResolutionRoot (CLAUDE.md: decisions are Rules). The world adapter
    writes dhyp_recent + recognition_frac, sets resolution_eval_pending=1, and
    fires it. Returns {'root', 'rule_index'}."""
    nat = _native(substrate)
    try:
        substrate.add_production({
            "src": {"type": "AcousticResolutionRoot", "var": "a"},
            "edge_type": "manages",
            "tgt": {"type": "AcousticResolutionRoot", "var": "b"},
            "provenance": "acoustic_resolution:self"})
    except Exception:
        pass
    root = _root(substrate)
    a = substrate.node(root)["attrs"]
    for k, v in (("dhyp_recent", 0), ("recognition_frac", 0.0),
                 ("resolution_eval_pending", 0)):
        if k not in a:
            substrate.set_attr(root, k, v)
    if root not in substrate.neighbours(root, "manages"):
        try:
            substrate.add_edge(root, "manages", root, {})
        except Exception:
            pass
    sat_next, res_next = _resolution_rule_terms()
    R = Var("R")
    rule = {
        "name": "manage_acoustic_resolution",
        "match": [["R", "manages", "R"]],
        "where": Eq(a=Attr(R, "resolution_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "R", "resolution", {"__term__": res_next.to_dict()}],
            ["set_attr", "R", "saturation_cycles",
             {"__term__": sat_next.to_dict()}],
            ["set_attr", "R", "resolution_eval_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def step_resolution(substrate, dhyp_recent: int, recognition_frac: float,
                    rule_index: int) -> int:
    """Adapter: record the cycle's observations onto the root + fire the agent's
    graph-resident resolution rule (the DECISION lives in the rule, not here).
    Returns the (possibly stepped-up) resolution."""
    root = _root(substrate)
    substrate.set_attr(root, "dhyp_recent", int(dhyp_recent))
    substrate.set_attr(root, "recognition_frac", float(recognition_frac))
    substrate.set_attr(root, "resolution_eval_pending", 1)
    _native(substrate).apply_rule_once(rule_index)
    return get_resolution(substrate)


def install_resolution_knowledge(substrate) -> dict:
    """Install the agent's graph-resident KNOWLEDGE that its acoustic resolution
    is a thing it controls + the rule for fixing it. A Concept in the phonology
    Mt, same shape as the development concepts (description + rule + indicator)."""
    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "phonology":
            mt = n
            break
    name = "acoustic_resolution"
    cid = None
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            cid = c
            break
    desc = ("The agent's discriminative feature space is bounded by how finely it "
            "resolves the cochlear TRAJECTORY (the full 800-value 32-frame x "
            "25-patch signal every AcousticSign carries) into frequency bands. "
            "The coarse low/mid/high summaries are only 3 of up to 25 bands — the "
            "fine data is always present, just unused. Resolution is NOT a fixed "
            "limit; it is a dial the agent owns (AcousticResolutionRoot.resolution).")
    rule = ("When discriminative invention DRIES to a trickle (no new "
            "discriminative_feature_needed hypotheses) for several cycles WHILE "
            "recognition is still poor, the bands — not the features — are the "
            "bottleneck: step the resolution UP the ladder (3->6->12->25) to "
            "expose finer bands the next round can split on. Don't keep retrying "
            "invention at a resolution that's run out of dimensions.")
    if cid is None:
        cid = substrate.add_node("Concept", {
            "name": name, "description": desc, "rule": rule,
            "indicator": "discriminative_hyps_recent_vs_recognition",
            "origin": "acoustic_resolution_knowledge"})
    else:
        substrate.set_attr(cid, "description", desc)
        substrate.set_attr(cid, "rule", rule)
    if mt is not None and cid not in substrate.neighbours(mt, "contains"):
        try:
            substrate.add_edge(mt, "contains", cid)
        except Exception:
            pass
    _root(substrate)   # ensure the dial node exists
    return {"concept": cid}


__all__ = ["get_resolution", "band_names", "enrich_sign_bands",
           "enrich_sign_windows", "enrich_sign_fft", "fft_resolution",
           "fft_band_centre_hz",
           "install_resolution_management_rule", "step_resolution",
           "install_resolution_knowledge", "_root"]

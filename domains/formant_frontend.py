"""Warped formant-dense cochlear front-end — mechanical generator.

The AGENT specified this (domains.runtime_design.agent_specify_frontend):
its ArgMax-over-cochlear-bands formant is blunt because only ~16 of its
32 log-spaced bands (80-7500 Hz) fall in the formant region (250-2500 Hz),
while F1/F2 sit ~100-200 Hz apart there. It asked to *warp the log layout
to oversample the formant region* and *raise the A1 patch count*.

This module is the mechanical generator that turns that spec into a
concrete center-frequency list and an enlarged A1 patch library. It makes
no decisions — the agent decides WHAT (oversample 250-2500 Hz, more
patches); this emits HOW (the fc list, the patch dicts). It is a pure
world-adapter helper: it produces config the STT pipeline sets when it
mints gammatone / patch_evaluate Operation nodes. No new Rust; the same
gammatone primitive, just more of them at formant-region fc.
"""
from __future__ import annotations

import math


def warped_band_centres(
    n_bands: int = 32,
    formant_lo_hz: float = 250.0,
    formant_hi_hz: float = 2500.0,
    formant_fraction: float = 0.80,
    full_lo_hz: float = 80.0,
    full_hi_hz: float = 7500.0,
) -> list[float]:
    """Generate a warped log-tonotopic layout that OVERSAMPLES the
    formant region [formant_lo, formant_hi].

    Allocates ~``formant_fraction`` of the ``n_bands`` log-spaced
    *within* [formant_lo, formant_hi], and the remainder split across
    the sub-formant tail [full_lo, formant_lo] and the supra-formant
    tail [formant_hi, full_hi] (also log-spaced). The result spans the
    same 80-7500 Hz range as the default but with far denser sampling
    where F1/F2 live.

    Returns a sorted list of center frequencies (Hz). Same primitive
    (gammatone), more bands in the formant region.
    """
    n_formant = max(1, int(round(n_bands * formant_fraction)))
    n_rest = n_bands - n_formant
    # Split the remaining bands across the two tails proportional to
    # their log-width, so neither tail is starved.
    lo_w = math.log(formant_lo_hz) - math.log(full_lo_hz)
    hi_w = math.log(full_hi_hz) - math.log(formant_hi_hz)
    tot_w = lo_w + hi_w
    if tot_w <= 0 or n_rest <= 0:
        n_lo = n_hi = 0
        n_rest = 0
    else:
        n_lo = int(round(n_rest * (lo_w / tot_w)))
        n_hi = n_rest - n_lo

    def _logspace(lo, hi, n, include_hi):
        if n <= 0:
            return []
        llo, lhi = math.log(lo), math.log(hi)
        if include_hi and n > 1:
            return [math.exp(llo + (lhi - llo) * i / (n - 1)) for i in range(n)]
        # Endpoint-excluded so tails don't duplicate the formant edges.
        return [math.exp(llo + (lhi - llo) * (i + 1) / (n + 1)) for i in range(n)]

    bands: list[float] = []
    # Sub-formant tail (80 .. 250), endpoints excluded.
    bands += _logspace(full_lo_hz, formant_lo_hz, n_lo, include_hi=False)
    # Formant region (250 .. 2500), endpoints INCLUDED — dense.
    bands += _logspace(formant_lo_hz, formant_hi_hz, n_formant, include_hi=True)
    # Supra-formant tail (2500 .. 7500), endpoints excluded.
    bands += _logspace(formant_hi_hz, full_hi_hz, n_hi, include_hi=False)
    bands.sort()
    return bands


def warped_patch_library(
    centres_hz: list[float] | None = None,
    variants_per_centre: tuple[str, ...] = ("n", "m", "b", "f", "u", "d"),
) -> list[dict]:
    """Generate an enlarged A1 patch library at the given spectral
    centres (default: dense across the formant region). Mirrors the
    naming / variant scheme of the default 25-patch library so
    lexical_access's name-sorted channel order stays stable, but with
    more spectral centres concentrated in 250-2500 Hz — the agent asked
    to "raise the A1 patch count so the trajectory carries that finer
    frequency axis."

    Returns a list of patch dicts (same shape as
    domains.auditory_cortex._patch output).
    """
    if centres_hz is None:
        # Dense formant-region centres + the two tails, ~9 centres.
        centres_hz = [400, 650, 900, 1200, 1500, 1900, 2400, 3500, 5500]

    def _patch(name, kind, centre, sigma, dur, slope=0.0):
        return {"name": name, "kind": kind,
                "centre_hz": float(centre),
                "freq_sigma_hz": float(sigma),
                "duration_ms": float(dur),
                "slope_hz_per_ms": float(slope)}

    # Variant templates — sigma scales with centre (constant-Q-ish),
    # matching the default library's broadening with frequency.
    out: list[dict] = []
    for c in centres_hz:
        cc = int(round(c))
        sig_n = max(120.0, 0.20 * c)
        sig_m = max(250.0, 0.40 * c)
        sig_b = max(450.0, 0.65 * c)
        templates = {
            "n": ("sustained", sig_n, 80, 0.0),
            "m": ("sustained", sig_m, 80, 0.0),
            "b": ("sustained", sig_b, 80, 0.0),
            "f": ("burst",     sig_m, 20, 0.0),
            "u": ("fm",        sig_n, 60, +0.015 * c),
            "d": ("fm",        sig_n, 60, -0.015 * c),
        }
        for v in variants_per_centre:
            kind, sigma, dur, slope = templates[v]
            out.append(_patch(f"p{cc:04d}_{v}", kind, cc, sigma, dur, slope))
    return out


__all__ = ["warped_band_centres", "warped_patch_library"]

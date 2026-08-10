"""A1 cortex tests — verify that different acoustic inputs light up
different patches in the starter library. This is the core
discrimination test: if the cortex layer is working, a sibilant
sound makes the sibilant patch respond above the others, a vowel-
like tone makes the voiced patch respond, etc.
"""
from __future__ import annotations

import numpy as np
import pytest

srs = pytest.importorskip("substrate_rs")

from domains.auditory_cortex import _DEFAULT_PATCHES
from domains.auditory_cortex_adapter import AcParams, process_audio
from substrate.seed_loader import manifest_for

# Patch names encode their centre frequency as a `pXXXX` prefix
# (p0400 = 400 Hz … p5500 = 5500 Hz). The biology-grounded library
# replaced the six hand-named patches (voiced/sibilant/…) with a grid
# of 5 centres × variants; discrimination now reads at the centre level.
_LOW_CENTRE = "p0400"    # voiced / vowel range
_HIGH_CENTRE = "p5500"   # sibilant range


_FS = 22050
_BANDS = [200.0, 400.0, 800.0, 1500.0, 3000.0, 6000.0]


def _attach(sub):
    for seed_id in ("audio", "cochlear_nucleus", "inferior_colliculus",
                      "auditory_cortex"):
        try:
            sub.load_seed_manifest(manifest_for(seed_id))
        except Exception:
            pass


def _tone_burst(hz: float, duration_s: float = 0.5,
                  fs: int = _FS) -> np.ndarray:
    """A simple sustained tone."""
    n = int(duration_s * fs)
    t = np.arange(n, dtype=np.float32) / fs
    a = max(1, int(0.02 * fs))
    ramp = np.linspace(0, 1, a, dtype=np.float32)
    x = (0.4 * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    x[:a] *= ramp
    x[-a:] *= ramp[::-1]
    return x


def _bandlimited_noise(duration_s: float = 0.5, fs: int = _FS,
                         lo_hz: float = 0.0,
                         hi_hz: float | None = None) -> np.ndarray:
    """Brick-wall band-limited noise via FFT mask. Clean spectrum
    isolation — exactly the test-stimulus shape A1 patches need to
    discriminate."""
    n = int(duration_s * fs)
    rng = np.random.default_rng(42)
    x = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    mask = freqs >= lo_hz
    if hi_hz is not None:
        mask &= freqs <= hi_hz
    spec *= mask
    y = np.fft.irfft(spec, n=n).astype(np.float32)
    # Renormalise so peak ≈ 0.4.
    peak = float(np.max(np.abs(y)) or 1.0)
    return (0.4 * y / peak).astype(np.float32)


def _peaks_by_patch(sub, stream) -> dict[str, float]:
    """Map each patch name to its A1Response peak attr."""
    out: dict[str, float] = {}
    for resp in sub.neighbours(stream, "has_a1_response"):
        a = sub.node(resp)["attrs"]
        out[a["patch_name"]] = float(a["peak"])
    return out


def _max_peak_at_centre(peaks: dict[str, float], centre: str) -> float:
    """Strongest response among the variant patches at one centre
    frequency (names share a `pXXXX` prefix)."""
    vals = [v for name, v in peaks.items() if name.startswith(centre)]
    return max(vals) if vals else 0.0


def _argmax_centre(peaks: dict[str, float]) -> str:
    """Centre-frequency prefix with the strongest single patch."""
    best, best_v = "", float("-inf")
    for name, v in peaks.items():
        c = name.split("_")[0]
        if v > best_v:
            best, best_v = c, v
    return best


def test_seed_installs_default_patch_library():
    """The seed lands the full biology-grounded patch library."""
    sub = srs.Substrate()
    _attach(sub)
    patches = list(sub.nodes("A1Patch"))
    assert len(patches) == len(_DEFAULT_PATCHES)
    names = {sub.node(p)["attrs"]["name"] for p in patches}
    assert names == {p["name"] for p in _DEFAULT_PATCHES}


def test_one_response_node_per_patch():
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _tone_burst(800.0)
    summary = process_audio(sub, stream, samples, _FS, _BANDS)
    assert summary["responses"] == len(_DEFAULT_PATCHES)  # one per patch


def test_high_freq_noise_drives_sibilant_patch():
    """High-frequency band-limited noise (3-8 kHz) should drive
    the high-centre (sibilant-range) patches above the low-centre
    (voiced-range) patches. The core discrimination test:
    different-spectrum inputs → different cortical patches respond."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _bandlimited_noise(duration_s=0.5,
                                    lo_hz=3000.0, hi_hz=8000.0)
    process_audio(sub, stream, samples, _FS, _BANDS)
    peaks = _peaks_by_patch(sub, stream)
    high = _max_peak_at_centre(peaks, _HIGH_CENTRE)
    low = _max_peak_at_centre(peaks, _LOW_CENTRE)
    assert high > low * 1.5, (
        f"high-freq noise should drive {_HIGH_CENTRE} > {_LOW_CENTRE}; "
        f"got high={high:.3f} low={low:.3f}")


def test_low_freq_tone_drives_voiced_patch():
    """A 400 Hz tone should drive the low-centre (voiced-range)
    patches hardest: they hold the global argmax and outrun the
    high-centre (sibilant-range) patches."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _tone_burst(400.0, duration_s=0.5)
    process_audio(sub, stream, samples, _FS, _BANDS)
    peaks = _peaks_by_patch(sub, stream)
    low = _max_peak_at_centre(peaks, _LOW_CENTRE)
    high = _max_peak_at_centre(peaks, _HIGH_CENTRE)
    assert _argmax_centre(peaks) == _LOW_CENTRE, (
        f"400 Hz tone's strongest patch should be at {_LOW_CENTRE}; "
        f"got argmax {_argmax_centre(peaks)} from {peaks}")
    assert low > high, (
        f"400 Hz tone should drive {_LOW_CENTRE} > {_HIGH_CENTRE}; "
        f"got low={low:.3f} high={high:.3f}")


def test_responses_link_back_to_patches():
    """Every A1Response has a for_patch edge to its source A1Patch —
    graph-level audit trail."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _tone_burst(800.0)
    process_audio(sub, stream, samples, _FS, _BANDS)
    for resp in sub.neighbours(stream, "has_a1_response"):
        patches = list(sub.neighbours(resp, "for_patch"))
        assert len(patches) == 1
        # The response's patch_name attr matches the linked patch's
        # name attr.
        ra = sub.node(resp)["attrs"]
        pa = sub.node(patches[0])["attrs"]
        assert ra["patch_name"] == pa["name"]


def test_a1_pipeline_is_graph_resident():
    """The A1 pipeline is graph data: one patch_evaluate op per
    A1Patch, wired by feeds_into from every cochlear envelope op,
    plus a downstream schmitt_peaks per patch for A1Event minting.
    The agent can read it."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _tone_burst(800.0)
    process_audio(sub, stream, samples, _FS, _BANDS)

    n_bands = len(_BANDS)
    n_patches = len(_DEFAULT_PATCHES)  # the default library

    by_kind: dict[str, list] = {}
    for op in sub.nodes("Operation"):
        kind = sub.node(op)["attrs"]["kind"]
        by_kind.setdefault(kind, []).append(op)

    assert len(by_kind["patch_evaluate"]) == n_patches
    # Each patch_evaluate has every cochlear envelope as a
    # feeds_into predecessor.
    for pe in by_kind["patch_evaluate"]:
        preds = list(sub.in_neighbours(pe, "feeds_into"))
        env_count = sum(
            1 for p in preds
            if sub.node(p)["attrs"].get("kind") == "envelope"
        )
        assert env_count == n_bands

    # Each patch_evaluate carries a for_patch edge to its A1Patch.
    for pe in by_kind["patch_evaluate"]:
        patches = list(sub.neighbours(pe, "for_patch"))
        assert len(patches) == 1
        assert sub.node(patches[0])["type"] == "A1Patch"


def test_events_link_back_to_responses():
    """A1Events trace back to their A1Response via from_response."""
    sub = srs.Substrate()
    _attach(sub)
    stream = sub.add_node("AudioStream",
                            {"codec": "raw_pcm", "sample_rate": _FS})
    samples = _tone_burst(800.0, duration_s=0.5)
    process_audio(sub, stream, samples, _FS, _BANDS)
    events = list(sub.neighbours(stream, "has_a1_event"))
    if not events:
        pytest.skip("no events fired for this stimulus")
    for ev in events:
        resps = list(sub.neighbours(ev, "from_response"))
        assert len(resps) == 1
        assert sub.node(resps[0])["type"] == "A1Response"

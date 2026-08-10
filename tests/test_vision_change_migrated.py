"""THE CHANGE-DETECTION RUNG's gate (`VISION_CHANGE_PREREG.md`).

Guards the four things that can silently rot:
  1. §9 — `change=0` reproduces the median split EXACTLY (a live experiment
     depends on this; the concurrent Troxler run must not be perturbed).
  2. The median split IS the defect — `driven% == 50.00` exactly, in every
     regime. If this ever stops being exactly 50, the baseline moved.
  3. The regimes DIFFER under change detection, and none of them is 50.00.
  4. TRAP 2 (§13.1) — the sustained channel is ALIVE. A pure differentiator
     makes Troxler a tautology; the first cut of `ch_sustained` was INERT and
     only a per-channel control caught it. This test is that control, kept.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

H = W = 8


def _boot(change=0.0, sustain=1.0, seed=1):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    w = WaveWorld(s, h=H, w=W, seed=seed)
    cp = s.nodes("ChangeParams")
    assert len(cp) == 1, f"ChangeParams must be a singleton, got {len(cp)}"
    s.set_attr(cp[0], "change", float(change))
    s.set_attr(cp[0], "sustain", float(sustain))
    return s, w


def _driven(s, w):
    return np.mean([s.node(n)["attrs"].get("driven", 0.0) == 1.0
                    for n in w.cells.values()])


def _run(frames, **kw):
    s, w = _boot(**kw)
    out = []
    for f in frames:
        w.step(ignite_k=0, frame=f)
        out.append(_driven(s, w))
    return np.array(out), s, w


def _ramp(rng, n):
    """A drifting scene: an image translated a pixel at a time."""
    g = rng.random((H + 8, W + 8)).astype(np.float32)
    return [g[i:i + H, j:j + W].copy()
            for i, j in zip(range(n), range(n))]


def test_params_node_is_a_singleton_so_pickunique_cannot_panic():
    # §12.3: PickUnique PANICS on >1 candidate, deliberately. The adapter
    # find-or-creates for exactly this reason.
    s, _ = _boot()
    assert len(s.nodes("ChangeParams")) == 1
    # constructing a SECOND WaveWorld on the same substrate must not add another
    WaveWorld(s, h=4, w=4, seed=2)
    assert len(s.nodes("ChangeParams")) == 1


def test_default_off_reproduces_the_median_split_exactly():
    """§9. The default is the OLD behaviour: driven% is EXACTLY 50.00 — that is
    the defect, and it is preserved until a powered experiment retires it."""
    rng = np.random.default_rng(0)
    fr = [rng.random((H, W)).astype(np.float32) for _ in range(6)]
    d, _, _ = _run(fr, change=0.0)
    # An even cell count and a median split => exactly half, every step.
    assert np.allclose(d, 0.5), f"median split must be exactly 50%, got {d}"


def test_change_detection_is_not_a_median_split():
    """The whole point: `driven%` must stop being 50.00 and start depending on
    the regime. Exactly 50.00 is the tell that a new median split was built."""
    rng = np.random.default_rng(1)
    noise = [rng.random((H, W)).astype(np.float32) for _ in range(8)]
    stab = [np.full((H, W), 0.5, np.float32) for _ in range(8)]

    d_noise, _, _ = _run(noise, change=1.0, sustain=0.0)
    d_stab, _, _ = _run(stab, change=1.0, sustain=0.0)

    # dynamic noise: nearly everything changes by more than its own noise floor
    assert d_noise[2:].mean() > 0.9, d_noise
    # a stabilised field: a pure change detector CANNOT fire
    assert d_stab[2:].mean() == 0.0, d_stab
    # and neither is the 50.00 the median split asserted
    assert not np.allclose(d_noise[2:], 0.5)


def test_sustained_channel_is_alive_so_troxler_is_not_a_tautology():
    """TRAP 2 / §13.1 — THE test of this rung.

    A pure differentiator makes fading true BY CONSTRUCTION. The sustained
    channel must keep the retina firing on a PERFECTLY stabilised image, so the
    model PREDICTS NO retinal fading and can therefore be wrong.

    The first `ch_sustained` used a cumulative-mean TEMPORAL reference and was
    INERT (its first sample set ref = value exactly, so deviation was 0 forever)
    — §13.2's disease, and it would have made the model a differentiator wearing
    a sustained channel's clothes. This asserts the fix: a SPATIAL
    centre-surround contrast, which has no time argument to adapt away.
    """
    # A stabilised image WITH spatial structure (a vertical edge). Note a FLAT
    # field would have no centre-surround contrast and would fire nothing —
    # which is correct, and is why this fixture has an edge in it.
    edge = np.zeros((H, W), np.float32)
    edge[:, W // 2:] = 1.0
    frames = [edge.copy() for _ in range(8)]

    d_transient, _, _ = _run(frames, change=1.0, sustain=0.0)
    d_sustained, _, _ = _run(frames, change=1.0, sustain=1.0)

    # the tautology arm: a pure differentiator is SILENT on a stabilised image
    assert d_transient[2:].mean() == 0.0, d_transient
    # the default arm: the sustained channel keeps firing, FOREVER, on the edge
    assert d_sustained[-1] > 0.0, d_sustained
    # and it does not decay away over the run — no time argument to adapt on
    assert d_sustained[-1] == pytest.approx(d_sustained[2], abs=1e-9)


def test_each_drive_rule_has_its_own_phase_key():
    """A SHARED phase key would let whichever rule fired first block the others
    for that cell — ON would silence OFF and sustained, and the channels would
    stop being independently measurable. Also: a rule whose effect does not
    change its own match re-fires forever under the adapter's fixed-point loop
    (it hung the bench), so the guards must exist at all."""
    import json
    with open(os.path.join(ROOT, "seeds", "vision_change.json")) as fh:
        seed = json.load(fh)
    keys = []
    for r in seed["rules"]:
        stamped = [e[2] for e in r["effects"]
                   if e[0] == "set_attr" and str(e[2]).endswith("step")
                   or (e[0] == "set_attr" and str(e[2]).startswith("dstep"))]
        keys.extend(stamped)
    assert len(keys) == len(set(keys)), f"phase keys must be distinct: {keys}"
    assert len(keys) == 5, keys

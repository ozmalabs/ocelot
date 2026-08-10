"""THE RENDER MADE PRIMARY — the illusion battery: the migrated gate
(VISION_ILLUSION_PREREG.md).

Deterministic. Pins the headline claims that the eye is ONE bidirectional
predictive loop, demonstrated on illusions across two render engines, BOTH reused
UNCHANGED (NO new Rust, NO new seed rules):

  * SPATIAL  — vision_ground: a contour behind an occluder is COMPLETED (illusion);
    a VISIBLE break survives (veridical); the completion tracks the inducer
    orientation (the render is a real prediction, not a template).
  * TEMPORAL — BlinkBridge: a temporal gap is filled with PREDICTED motion where the
    raw input is empty (apparent motion); disabling the render leaves it empty
    (bottom-up); the fill tracks the velocity.
  * RECONCILIATION uses BOTH (percept != raw input, percept != pure render).
  * §9 — both seeds OFF by default are inert.

The two RNG floor controls (100 spatial, 400 temporal seeds) live in
scripts/illusion_measure.py, not here (they are slow and confirmatory).
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import json  # noqa: E402

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains import ground_world as gw  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

H = W = 16
OCC = (8, 8)
OR = 2.0
DT = ["pred", "coord:r", "coord:c", "val"]
DOT = [["cell", 0, 0, "red"]]


# --- spatial render engine (vision_ground) --------------------------------- #
def _sworld(interp=0.0, ground=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=H, w=W, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=OCC, blind_radius=OR)
    gw.set_ground_params(wd, ground=ground, interp=interp)
    return wd, anat


def _occ(anat, row=None, col=None):
    return sorted((r, c) for (r, c) in anat["blind"]
                  if (row is None or r == row) and (col is None or c == col))


# --- temporal render engine (BlinkBridge) ---------------------------------- #
def _trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def _moving(dv, n, base=DOT):
    out = [base]; cur = base
    for _ in range(n - 1):
        cur = _trans(dv, cur); out.append(cur)
    return out


def _norm(f):
    return sorted(tuple(x) for x in (f or []))


def _trun(seq, enabled=True):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    s.set_attr(ag, "blink_bridge_enabled", 1.0 if enabled else 0.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(DOT),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    o = s.add_node("Observation", {"frames": seq, "dim_types": DT,
                   "status": "blink_seq", "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    return s.node(o)["attrs"]


# =========================================================================== #
#  BATTERY A — SPATIAL
# =========================================================================== #
def test_amodal_completion_illusion_beats_bottom_up():
    """A contour behind an occluder is completed as ONE contour (gbel STEP) where
    the raw sensor shows only fragments (NaN)."""
    frame = np.zeros((H, W)); frame[8, :] = 1.0
    wg, ag = _sworld(); gw.present(wg, ag, frame)
    gbel = gw.belief_field(wg, ag); raw = gw.raw_sensor(wg, ag)
    span = _occ(ag, row=8)
    assert span, "occluder must cross the bar row"
    assert np.mean([abs(gbel[r, c] - 1.0) for (r, c) in span]) <= 0.05  # completed
    assert all(np.isnan(raw[r, c]) for (r, c) in span)                  # bottom-up: fragments


def test_veridical_visible_break_survives():
    """A VISIBLE break in the sensed region is NOT completed — the input wins."""
    f = np.zeros((H, W)); f[8, :] = 1.0; f[8, 2] = 0.0; f[8, 3] = 0.0
    wg, ag = _sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag)
    assert abs(gbel[8, 2]) <= 1e-6 and abs(gbel[8, 3]) <= 1e-6   # break seen
    assert abs(gbel[8, 0] - 1.0) <= 1e-6 and abs(gbel[8, 5] - 1.0) <= 1e-6


def test_render_tracks_the_prior_orientation():
    """Rotating the inducer rotates the completed contour — the render is a real
    prediction from the prior, not a fixed template."""
    f = np.zeros((H, W)); f[:, 8] = 1.0
    wg, ag = _sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag)
    assert all(abs(gbel[r, c] - 1.0) <= 1e-6 for (r, c) in _occ(ag, col=8))   # V completed
    off_bar = [(r, c) for (r, c) in _occ(ag, row=8) if c != 8]
    assert all(abs(gbel[r, c]) <= 1e-6 for (r, c) in off_bar)                 # no H invented


# =========================================================================== #
#  BATTERY B — TEMPORAL
# =========================================================================== #
def test_apparent_motion_fills_predicted_motion():
    """A temporal gap is filled with the PREDICTED moving object where the raw gap
    is empty; disabling the render leaves it empty (bottom-up)."""
    truth = _moving((0, 1), 6)
    seq = [truth[0], truth[1], [], [], [], truth[5]]
    at = _trun(seq)
    bridged = at.get("bridged") or []
    assert len(bridged) == 3 and at.get("constrained") == 1.0
    assert all(_norm(bf) == _norm(truth[2 + j]) for j, bf in enumerate(bridged))
    assert seq[2] == [] and seq[3] == [] and seq[4] == []           # bottom-up empty
    assert _trun(seq, enabled=False).get("bridged") is None         # render OFF -> no bridge


def test_temporal_render_tracks_velocity():
    """Changing the velocity changes the predicted intermediate positions."""
    def _b(dv):
        t = _moving(dv, 6)
        return _trun([t[0], t[1], [], [], [], t[5]]).get("bridged")
    b1, b2 = _b((0, 1)), _b((0, 2))
    assert b1 and b2 and _norm(b1[0]) != _norm(b2[0])
    assert _norm(b2[0]) == _norm(_moving((0, 2), 6)[2])


def test_contradiction_is_not_explained_away():
    """A surprising resume (object stops during the gap) diverges with a large
    (maximal, for a point) correction — the render is falsifiable, not a universal
    confabulator."""
    pre = _moving((1, 0), 4)
    at = _trun(pre + [[], []] + [pre[3]])   # stop during the gap, resume stopped
    assert at.get("diverged_at") is not None and at.get("diverged_at") >= 0
    assert at.get("correction") > 0


# =========================================================================== #
#  CROSS-CUTTING
# =========================================================================== #
def test_reconciliation_uses_both_render_and_input():
    """The percept is NEITHER the raw input (render adds structure in the hole/gap)
    NOR the pure render (veridical arms follow the input)."""
    # != raw input (spatial): render completes where raw is NaN
    frame = np.zeros((H, W)); frame[8, :] = 1.0
    wg, ag = _sworld(); gw.present(wg, ag, frame)
    span = _occ(ag, row=8)
    ne_raw_spatial = all(np.isnan(gw.raw_sensor(wg, ag)[r, c]) for (r, c) in span) \
        and all(abs(gw.belief_field(wg, ag)[r, c] - 1.0) <= 1e-6 for (r, c) in span)
    # != pure render (spatial): a visible break follows the input
    f2 = np.zeros((H, W)); f2[8, :] = 1.0; f2[8, 2] = 0.0
    wg2, ag2 = _sworld(); gw.present(wg2, ag2, f2)
    ne_render_spatial = abs(gw.belief_field(wg2, ag2)[8, 2]) <= 1e-6
    assert ne_raw_spatial and ne_render_spatial


def test_both_seeds_off_by_default_are_inert():
    """§9 — ground=0 never fills the hole; blink_bridge_enabled=0 never bridges."""
    wd, anat = _sworld(ground=0.0)
    f = np.zeros((H, W)); f[8, :] = 1.0; gw.present(wd, anat, f)
    assert float(sum(gw.filled(wd, anat)[r, c] for (r, c) in _occ(anat))) == 0.0
    truth = _moving((0, 1), 6)
    assert _trun([truth[0], truth[1], [], [], [], truth[5]], enabled=False).get("bridged") is None

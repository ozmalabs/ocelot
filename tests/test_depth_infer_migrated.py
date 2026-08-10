"""DEPTH AS AN INFERRED DIMENSION — the migrated gate (VISION_DEPTH_PREREG.md).

Monocular structure-from-motion: the residual of TimeInfer's single-generator
question, read as discrete depth. Proves the `DepthInfer` Term + the `depth_axis`
seed: a MULTI-DEPTH motion field (>=2 distinct surface velocities) mints a
`latent:depth` dimension ordered near->far by speed and predicts an unseen view;
a FLAT scene (one velocity everywhere — even multi-colour) mints NOTHING (the
decisive anti-forced control); shuffled/non-rigid grounds; different structures
give different orderings (frozen, §13.1); flag OFF is inert (§9).
"""
import json
import random

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
RED = [["cell", 0, 0, "red"],  ["cell", 1, 0, "red"],  ["cell", 2, 1, "red"]]
BLU = [["cell", 0, 1, "blue"], ["cell", 1, 1, "blue"], ["cell", 2, 0, "blue"]]
GRN = [["cell", 0, 0, "green"], ["cell", 1, 1, "green"], ["cell", 2, 0, "green"]]


def _trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def _scene(specs, n=6):
    surfs = [list(b) for b, _ in specs]
    out = []
    for _ in range(n):
        frame = []
        for s in surfs:
            frame += [list(x) for x in s]
        out.append(frame)
        surfs = [_trans(v, s) for s, (_, v) in zip(surfs, specs)]
    return out


def _boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("depth_axis"), ag)
    if enabled:
        s.set_attr(ag, "depth_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(RED + BLU),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    return s, ag, native


def _run(enabled, frames):
    s, ag, native = _boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = [dict(n_layers=s.node(n)["attrs"].get("n_layers"),
                velocities=tuple(tuple(v) for v in (s.node(n)["attrs"].get("velocities") or ())),
                ordering=tuple(tuple(x) for x in (s.node(n)["attrs"].get("ordering") or ())),
                window=s.node(n)["attrs"].get("window"))
           for n in s.nodes("LatentDimension") if s.node(n)["attrs"].get("name") == "latent:depth"]
    return at, lds


def test_multidepth_mints_latent_depth_ordered_by_velocity():
    at, lds = _run(True, _scene([(RED, (2, 0)), (BLU, (1, 0))], 6))
    assert at.get("status") == "depth_inferred"
    assert len(lds) == 1
    assert lds[0]["n_layers"] == 2
    assert lds[0]["velocities"] == ((2, 0), (1, 0))                 # near->far by speed
    assert lds[0]["ordering"] == (("cell", "red"), ("cell", "blue"))
    assert lds[0]["window"] == 6


def test_flat_scene_mints_nothing_the_decisive_control():
    # one velocity everywhere -> ONE generator carries the scene -> residual ZERO.
    at, lds = _run(True, _scene([(RED, (2, 0))], 6))
    assert at.get("status") == "depth_none"
    assert lds == []


def test_multicolour_single_velocity_mints_nothing():
    # two distinguishable surfaces but ONE velocity: appearance alone is NOT depth
    # (depth is minted from velocity VARIATION, never from multiple regions).
    at, lds = _run(True, _scene([(RED, (2, 0)), (BLU, (2, 0))], 6))
    assert at.get("status") == "depth_none"
    assert lds == []


def test_different_structures_give_different_orderings_frozen():
    # §13.1: same frozen Term, DIFFERENT correct ordering per scene (not forced).
    _, a = _run(True, _scene([(RED, (2, 0)), (BLU, (1, 0))], 6))       # red near
    _, b = _run(True, _scene([(RED, (1, 0)), (BLU, (3, 0))], 6))       # blue near
    _, c = _run(True, _scene([(RED, (3, 0)), (BLU, (2, 0)), (GRN, (1, 0))], 6))  # 3 layers
    assert a[0]["ordering"] == (("cell", "red"), ("cell", "blue"))
    assert b[0]["ordering"] == (("cell", "blue"), ("cell", "red"))
    assert c[0]["n_layers"] == 3
    assert len({a[0]["ordering"], b[0]["ordering"], c[0]["ordering"]}) == 3


def test_dedup_shared_velocity_compresses_layer_count():
    # 3 surfaces, 2 distinct velocities -> n_layers=2 (the MDL dedup).
    _, lds = _run(True, _scene([(RED, (3, 0)), (BLU, (3, 0)), (GRN, (1, 0))], 6))
    assert len(lds) == 1
    assert lds[0]["n_layers"] == 2
    assert len(lds[0]["ordering"]) == 3          # all three surfaces indexed


def test_shuffled_multidepth_grounds_at_the_longest_window():
    ob = _scene([(RED, (2, 0)), (BLU, (1, 0))], 8)
    spurious = 0
    for i in range(40):
        random.seed(27100 + i)
        sh = [list(f) for f in ob]; random.shuffle(sh)
        at, lds = _run(True, sh)
        if lds and sh != ob and sh != ob[::-1]:
            spurious += 1
    assert spurious == 0


def test_minted_depth_predicts_an_unseen_view_and_is_load_bearing():
    specs = [(RED, (2, 0)), (BLU, (1, 0))]
    frames6 = _scene(specs, 6)                    # f0..f5 seen; K=6
    withheld = []
    for b, v in specs:
        withheld += [list(x) for x in _trans((v[0] * 6, v[1] * 6), b)]
    withheld = sorted(tuple(x) for x in withheld)
    on, on_lds = _run(True, frames6)
    off, off_lds = _run(False, frames6)
    assert sorted(tuple(x) for x in on.get("predicted")) == withheld
    assert len(on_lds) == 1 and off_lds == []     # D_mint > 0
    assert on.get("predicted") is not None and off.get("predicted") is None  # D_pred > 0


def test_flag_off_is_inert():
    at, lds = _run(False, _scene([(RED, (2, 0)), (BLU, (1, 0))], 6))
    assert at.get("status") == "depth_seq"
    assert lds == []

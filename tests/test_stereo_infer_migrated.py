"""STEREO — DEPTH FROM N SIMULTANEOUS EYES — the migrated gate (VISION_STEREO_PREREG.md).

Stereo is the DEPTH operation on a SPATIAL frame-pair: N eyes view one scene at a
SINGLE instant; disparity is the inter-eye TRANSLATE (near large, far small); its
variation across surfaces IS depth. This gate proves the HEADLINE: the UNCHANGED
`DepthInfer` Term + the UNCHANGED `depth_axis` seed, fed EYE-frames, mint the SAME
`latent:depth` they mint from TICK-frames — frame-source is the only difference (no
`StereoInfer` delta, no new Rust, no new seed). The eye count falls out of
Count(Eye hubs), never a literal (BUILD FOR N: N=2 AND N=3); a single-depth scene
mints NOTHING; N=3 is more precise than N=2; the minted depth predicts an UNSEEN
eye; stereo depth == motion depth (same dimension).
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


def _boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("depth_axis"), ag)   # UNCHANGED depth seed
    if enabled:
        s.set_attr(ag, "depth_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(RED + BLU),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    return s, ag, native


def _eyes_from_graph(s):
    """Count(Eye hubs), ordered by baseline — the cardinality, from the graph."""
    return sorted(int(s.node(e)["attrs"]["baseline"]) for e in s.nodes("Eye"))


def _project(scene, baseline):
    frame = []
    for cells, disp in scene:
        for _, r, c, v in cells:
            frame.append(["cell", r, c - baseline * disp, v])
    return frame


def _run_stereo(enabled, scene, n_eyes):
    """Instantiate N Eye hubs, assemble one frame per hub FROM THE GRAPH, feed the
    depth_seq Observation the depth rung uses. Returns (attrs, lds, count_from_graph)."""
    s, ag, native = _boot(enabled)
    for b in range(n_eyes):
        s.add_node("Eye", {"baseline": float(b)})
    frames = [_project(scene, b) for b in _eyes_from_graph(s)]
    count_from_graph = len(_eyes_from_graph(s))            # == Count(Eye hubs)
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
    return at, lds, count_from_graph, frames


def _run_frames(enabled, frames):
    s, ag, native = _boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = [dict(n_layers=s.node(n)["attrs"].get("n_layers"),
                ordering=tuple(tuple(x) for x in (s.node(n)["attrs"].get("ordering") or ())))
           for n in s.nodes("LatentDimension") if s.node(n)["attrs"].get("name") == "latent:depth"]
    return at, lds


def test_eyeframes_mint_the_same_latent_depth_as_tickframes():
    # THE HEADLINE: unchanged DepthInfer + unchanged depth_axis, fed EYE frames,
    # mint latent:depth ordered near->far by disparity (frame-source only difference).
    at, lds, count, _ = _run_stereo(True, [(RED, 2), (BLU, 1)], 3)
    assert at.get("status") == "depth_inferred"
    assert len(lds) == 1
    assert lds[0]["n_layers"] == 2
    assert lds[0]["velocities"] == ((0, -2), (0, -1))               # near (disp 2) -> far (disp 1)
    assert lds[0]["ordering"] == (("cell", "red"), ("cell", "blue"))


def test_single_depth_scene_mints_nothing_the_decisive_control():
    # uniform disparity (multi-colour, one depth) AND zero disparity (infinity)
    # -> ONE inter-eye generator carries every eye -> residual ZERO -> NO mint.
    at2, l2, _, _ = _run_stereo(True, [(RED, 2), (BLU, 2)], 2)
    at3, l3, _, _ = _run_stereo(True, [(RED, 2), (BLU, 2)], 3)
    at0, l0, _, _ = _run_stereo(True, [(RED, 0), (BLU, 0)], 3)      # scene at infinity
    assert at2.get("status") == at3.get("status") == at0.get("status") == "depth_none"
    assert l2 == l3 == l0 == []


def test_eye_count_read_from_graph_not_a_literal():
    # BUILD FOR N: the SAME machinery at N=2 and N=3, count read from the graph,
    # frames.len() == Count(Eye hubs), orderings agree (no hardcoded 2).
    at2, l2, c2, f2 = _run_stereo(True, [(RED, 2), (BLU, 1)], 2)
    at3, l3, c3, f3 = _run_stereo(True, [(RED, 2), (BLU, 1)], 3)
    assert c2 == 2 and c3 == 3                          # Count(Eye hubs) from the graph
    assert len(f2) == c2 and len(f3) == c3              # frames.len() == eye count
    assert l2 and l3 and l2[0]["ordering"] == l3[0]["ordering"] == (("cell", "red"), ("cell", "blue"))


def test_N3_is_more_precise_than_N2():
    # An INCONSISTENT-disparity surface (BLU offset -1 then -2 -- not a rigid depth).
    # N=2 has ZERO verification pairs and ACCEPTS (mints); N=3's extra baseline is a
    # verification pair that REJECTS (floors). More baselines ground depth tighter.
    def incon(n):
        red_off = [-2 * i for i in range(n)]
        blu_off = [0, -1, -3][:n]                       # deltas -1, -2 : inconsistent
        out = []
        for i in range(n):
            fr = [["cell", r, c + red_off[i], v] for _, r, c, v in RED]
            fr += [["cell", r, c + blu_off[i], v] for _, r, c, v in BLU]
            out.append(fr)
        return out
    at2, l2 = _run_frames(True, incon(2))
    at3, l3 = _run_frames(True, incon(3))
    assert at2.get("status") == "depth_inferred" and len(l2) == 1   # N=2 hallucinates a layer
    assert at3.get("status") == "depth_none" and l3 == []            # N=3 rejects it


def test_different_structures_give_different_orderings_frozen():
    _, a, _, _ = _run_stereo(True, [(RED, 2), (BLU, 1)], 3)          # red near
    _, b, _, _ = _run_stereo(True, [(RED, 1), (BLU, 3)], 3)          # blue near (reversed)
    _, c, _, _ = _run_stereo(True, [(RED, 3), (BLU, 2), (GRN, 1)], 3)  # 3 layers
    assert a[0]["ordering"] == (("cell", "red"), ("cell", "blue"))
    assert b[0]["ordering"] == (("cell", "blue"), ("cell", "red"))
    assert c[0]["n_layers"] == 3
    assert len({a[0]["ordering"], b[0]["ordering"], c[0]["ordering"]}) == 3


def test_eye_order_shuffle_grounds_at_the_longest_config():
    # mismatched eyes: scramble which eye's view sits at which sequence position.
    ob = [_project([(RED, 2), (BLU, 1)], b) for b in range(8)]       # N=8 longest config
    spurious = 0
    for i in range(40):
        random.seed(28000 + i)
        sh = [list(f) for f in ob]; random.shuffle(sh)
        _, lds = _run_frames(True, sh)
        if lds and sh != ob and sh != ob[::-1]:
            spurious += 1
    assert spurious == 0


def test_minted_depth_predicts_an_unseen_eye_and_is_load_bearing():
    scene = [(RED, 2), (BLU, 1)]
    full = [_project(scene, b) for b in range(4)]                    # eyes 0,1,2,3
    seen = full[:3]                                                  # feed eyes 0,1,2
    heldout = sorted(tuple(x) for x in full[3])                      # the UNSEEN eye 3
    on, on_lds = _run_frames(True, seen)
    off, off_lds = _run_frames(False, seen)
    assert sorted(tuple(x) for x in on.get("predicted")) == heldout
    assert len(on_lds) == 1 and off_lds == []                       # D_mint > 0
    assert on.get("predicted") is not None and off.get("predicted") is None  # D_pred > 0


def test_stereo_depth_equals_motion_depth_same_dimension():
    # ADDITIVE: the SAME depth structure ordered the SAME way whether grounded from
    # N eyes at one tick (stereo) or one eye over K ticks (motion).
    _, stereo_lds, _, _ = _run_stereo(True, [(RED, 2), (BLU, 1)], 3)
    # motion: one eye, surfaces translate by the same depth->speed map over ticks.
    def motion(specs, n):
        surfs = [list(b) for b, _ in specs]
        out = []
        for _ in range(n):
            fr = []
            for sfc in surfs:
                fr += [list(x) for x in sfc]
            out.append(fr)
            surfs = [[["cell", r + dv[0], c + dv[1], v] for _, r, c, v in sfc]
                     for sfc, (_, dv) in zip(surfs, specs)]
        return out
    _, motion_lds = _run_frames(True, motion([(RED, (0, -2)), (BLU, (0, -1))], 6))
    assert stereo_lds[0]["ordering"] == motion_lds[0]["ordering"]


def test_flag_off_is_inert():
    at, lds, _, _ = _run_stereo(False, [(RED, 2), (BLU, 1)], 3)
    assert at.get("status") == "depth_seq"
    assert lds == []

"""TIME AS AN INFERRED DIMENSION — the migrated gate (VISION_TIME_PREREG.md).

Deterministic; proves the `translate` generator kind + the `TimeInfer` Term +
the `time_axis` seed: an ordered motion orbit mints a `latent:time` dimension
whose exponent is time and which predicts an unseen frame; a shuffled /
varying-velocity sequence grounds at enumeration; different generator per
motion (frozen); flag OFF is inert (§9).
"""
import json
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def _lin(M, cs):
    rs = [c[1] for c in cs]; cc = [c[2] for c in cs]; mr, mc = min(rs), min(cc)
    return [["cell", M[0]*(r-mr)+M[1]*(c-mc), M[2]*(r-mr)+M[3]*(c-mc), v] for _, r, c, v in cs]


def _trans(dv, cs):
    return [["cell", r+dv[0], c+dv[1], v] for _, r, c, v in cs]


def _orbit(fn, n=7):
    out = [BASE]; cur = BASE
    for _ in range(n - 1):
        cur = fn(cur); out.append(cur)
    return out


def _boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    if enabled:
        s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _run(enabled, frames):
    s, ag, native = _boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = [(s.node(n)["attrs"].get("generator_kind"), tuple(s.node(n)["attrs"].get("offset") or ()),
            tuple(s.node(n)["attrs"].get("matrix") or ()), s.node(n)["attrs"].get("window"))
           for n in s.nodes("LatentDimension") if s.node(n)["attrs"].get("name") == "latent:time"]
    return at, lds


def test_ordered_orbit_mints_latent_time():
    at, lds = _run(True, _orbit(lambda c: _trans((2, 0), c), 7))
    assert at.get("status") == "time_inferred"
    assert lds == [("translate", (2, 0), (), 7)]


def test_multimotion_distinct_generator_per_motion():
    motions = {
        "translate(2,0)": (lambda c: _trans((2, 0), c), ("translate", (2, 0), ())),
        "translate(1,3)": (lambda c: _trans((1, 3), c), ("translate", (1, 3), ())),
        "shear":          (lambda c: _lin([1, 0, 1, 1], c), ("linear", (), (1, 0, 1, 1))),
        "rotate90":       (lambda c: _lin([0, -1, 1, 0], c), ("linear", (), (0, -1, 1, 0))),
        "scale2":         (lambda c: _lin([2, 0, 0, 2], c), ("linear", (), (2, 0, 0, 2))),
    }
    descs = set()
    for name, (fn, exp) in motions.items():
        n = 4 if name == "scale2" else 6
        _, lds = _run(True, _orbit(fn, n))
        assert len(lds) == 1, name
        assert (lds[0][0], lds[0][1], lds[0][2]) == exp, name
        descs.add((lds[0][0], lds[0][1], lds[0][2]))
    assert len(descs) == 5  # forced-signature ruled out (§13.1)


def test_shuffled_sequence_grounds_at_enumeration():
    import random
    ob = _orbit(lambda c: _lin([1, 0, 1, 1], c), 8)
    spurious = 0
    for i in range(40):
        random.seed(26100 + i)
        sh = ob[:]; random.shuffle(sh)
        at, lds = _run(True, sh)
        if lds and sh != ob[::-1]:
            spurious += 1
    assert spurious == 0


def test_varying_velocity_mints_an_order_2_generator():
    # SUPERSEDES the old `test_varying_velocity_is_not_an_orbit`, which asserted
    # this accelerating stream floors to `time_none` — the deliberate order-1
    # MDL floor. That floor is now RESOLVED by the DIMENSION-GENERIC order-N
    # capability (GENERIC_ORDER_N_RESULTS.md): the per-pair offset stream
    # (1,2,3,4,5,6) is not constant but its finite difference is, so the
    # recursion fits an ORDER-2 generator (acceleration) instead of flooring.
    # The control the old floor protected — a genuinely order-≥N-UNSTRUCTURED
    # (random) stream must still floor — is preserved in
    # test_generic_order_n_migrated.py::test_random_stream_floors.
    acc = [BASE]; cur = BASE
    for k in range(1, 7):
        cur = _trans((k, 0), cur); acc.append(cur)
    # Self-contained boot/run so the minted dimension's `order` attr is
    # readable (the shared `_run` returns only kind/offset/matrix/window).
    s, ag, native = _boot(True)
    o = s.add_node("Observation", {"frames": acc, "dim_types": DT,
                   "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    assert s.node(o)["attrs"].get("status") == "time_inferred"
    mints = [(s.node(n)["attrs"].get("generator_kind"), s.node(n)["attrs"].get("order"))
             for n in s.nodes("LatentDimension")
             if s.node(n)["attrs"].get("name") == "latent:time"]
    assert mints == [("translate", 2)]       # translate family, order-2 (accel)


def test_minted_axis_predicts_an_unseen_frame_and_is_load_bearing():
    frames7 = _orbit(lambda c: _trans((2, 0), c), 7)          # f0..f6
    withheld = sorted([tuple(x) for x in _trans((14, 0), BASE)])  # f7, unseen
    on, on_lds = _run(True, frames7)
    off, off_lds = _run(False, frames7)
    assert sorted([tuple(x) for x in on.get("predicted")]) == withheld
    assert len(on_lds) == 1 and off_lds == []          # D > 0, not decoration
    assert on.get("predicted") is not None and off.get("predicted") is None


def test_flag_off_is_inert():
    at, lds = _run(False, _orbit(lambda c: _trans((2, 0), c), 7))
    assert at.get("status") == "motion_seq"
    assert lds == []

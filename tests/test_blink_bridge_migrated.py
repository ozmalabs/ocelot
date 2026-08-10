"""THE BLINK — a temporal hole bridged by grounding: the migrated gate
(VISION_BLINK_PREREG.md). The temporal twin of the blind spot.

Deterministic. Proves the `BlinkBridge` Term + the `blink_bridge` seed under the
CONFABULATE-BY-DEFAULT semantics: a blink is ALWAYS filled with a best-guess
continuation; grounding only CONSTRAINS the guess. Under consistent motion the
guess is pinned to G^k(last) (== truth, not frozen) at confidence > 0 and the
percept is invisible (resume confirmed, correction 0); a change during the blink
is missed until divergence while a visible change is signalled at once; a long gap
is STILL filled (not refused) and the correction on divergence grows with the gap
while confidence decays; a prefix with no consistent motion STILL confabulates but
UNCONSTRAINED (confidence 0), not held open; flag OFF is inert (§9).
"""
import json

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def _trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def _moving(dv, n, base=BASE):
    out = [base]; cur = base
    for _ in range(n - 1):
        cur = _trans(dv, cur); out.append(cur)
    return out


def _blink(seq, ticks):
    return [([] if t in ticks else f) for t, f in enumerate(seq)]


def _norm(frame):
    return sorted(tuple(x) for x in (frame or []))


def _boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    if enabled:
        s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _run(enabled, frames):
    s, ag, native = _boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "blink_seq", "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    return s.node(o)["attrs"]


def test_blink_is_real_hole():
    # the blink frames carry NO data (empty) — a genuine temporal hole.
    seq = _blink(_moving((1, 0), 7), {3, 4})
    assert seq[3] == [] and seq[4] == [] and seq[2] and seq[5]


def test_grounding_constrains_guess_to_motion_not_frozen():
    truth = _moving((1, 0), 7)
    at = _run(True, _blink(truth, {3, 4}))
    assert at.get("status") == "blink_bridged"
    assert at.get("constrained") == 1.0 and at.get("confidence") > 0.0
    for j, bf in enumerate(at["bridged"]):
        tick = 3 + j
        assert _norm(bf) == _norm(truth[tick])                 # tracks the motion
        assert _norm(at["frozen"][j]) != _norm(truth[tick])    # freeze does NOT
        assert _norm(bf) != _norm(at["frozen"][j])             # guess != persistence


def test_bridge_tracks_the_generator():
    # change the pre-blink motion -> the bridge changes accordingly (GROUNDING,
    # not a stored default).
    a = _run(True, _blink(_moving((1, 0), 7), {3, 4}))
    b = _run(True, _blink(_moving((0, 2), 7), {3, 4}))
    assert _norm(a["bridged"][0]) != _norm(b["bridged"][0])
    assert _norm(b["bridged"][0]) == _norm(_moving((0, 2), 7)[3])


def test_consistent_motion_blink_is_invisible():
    at = _run(True, _blink(_moving((1, 0), 7), {3, 4}))
    assert at.get("status") == "blink_bridged"
    assert at.get("diverged_at") == -1        # resume confirms guess: no seam
    assert at.get("correction") == 0          # nothing to correct


def test_change_in_blink_is_missed_until_divergence():
    truth = _moving((1, 0), 7)
    # object stops at t3 (inside the blink); detected only when data returns (t5)
    stopped = truth[:3] + [truth[2]] * 4
    at = _run(True, _blink(stopped, {3, 4}))
    assert at.get("status") == "blink_bridged"
    assert at.get("diverged_at") == 5         # LATE — bridged over during the blink


def test_change_in_visible_frame_is_signalled_at_once():
    truth = _moving((1, 0), 7)
    # object stops at t6 (a visible frame, after the blink); detected immediately
    stopped_vis = truth[:6] + [truth[5]]
    at = _run(True, _blink(stopped_vis, {3, 4}))
    assert at.get("diverged_at") == 6         # latency 0: caught the instant seen


def test_long_gap_still_filled_confidence_decays():
    # NOT a refusal: a longer blink is STILL confabulated, at LOWER confidence
    # (relative decay: support / (support + gap)).
    def probe(gap):
        pre = _moving((1, 0), 4)          # confirm_run = 3
        resume = _moving((1, 0), 4 + gap + 1)[4 + gap]
        return _run(True, pre + [[]] * gap + [resume])
    short, long = probe(1), probe(6)
    assert short.get("status") == "blink_bridged" and short.get("bridged") is not None
    assert long.get("status") == "blink_bridged" and long.get("bridged") is not None
    assert long.get("confidence") < short.get("confidence")   # decays, not refuses


def test_no_consistent_motion_still_confabulates_but_unconstrained():
    # accelerating prefix: pairwise mutual-translates yet NOT one orbit. It STILL
    # fills (the seed of hallucination), but UNCONSTRAINED (confidence 0).
    acc = [BASE]; cur = BASE
    for k in range(1, 4):
        cur = _trans((k, 0), cur); acc.append(cur)
    at = _run(True, acc[:3] + [[], []])
    assert at.get("status") == "blink_bridged"
    assert at.get("bridged") is not None      # confabulates, not silent
    assert at.get("constrained") == 0.0       # but NOT pinned to a stable M
    assert at.get("confidence") == 0.0        # low-confidence guess


def test_flag_off_is_inert():
    at = _run(False, _blink(_moving((1, 0), 7), {3, 4}))
    assert at.get("status") == "blink_seq"    # §9: default preserves behaviour
    assert at.get("bridged") is None

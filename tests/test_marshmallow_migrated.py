"""BLOCK 240000 -- MARSHMALLOW DISSOLUTION gate. The wait/take decision is a graph
RULE (mm_choose, Argmax over candidate total_value) over the LANDED 204000
core_emotions value economy, riding the 207000 time-cost Drive (weight =
temperament). This file gates that temperament and the reliability-prior are
SEPARABLE causes of wait-time (the confound the wet marshmallow test cannot
escape), the decision is graph-native, and the new world is isolated
(byte-identity when absent)."""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.marshmallow_world import (        # noqa: E402
    MarshmallowWorld, predicted_wait_time)

CANON_MD5 = "a32ed336662eaa9eb6df27b7112541ac"   # canonical .so after native-only CAN cutover (Ising engine removed)


def test_wait_take_is_a_graph_rule_matching_the_formula():
    """The RULE mm_choose (Argmax over candidate total_value), NOT Python, produces
    wait-time; the swept graph decision reproduces the pre-registered analytic grid
    exactly."""
    temps, priors = [], []
    for p in (60, 80, 100):
        for w in (2, 4, 8):
            temps.append(w); priors.append(p)
    mw = MarshmallowWorld(temps, priors)
    wt = mw.wait_times()
    mw.close()
    exp = [predicted_wait_time(p, w) for p in (60, 80, 100) for w in (2, 4, 8)]
    assert wt == exp
    assert exp == [5, 3, 2, 15, 8, 4, 25, 13, 7]


def test_g_dissolution_temperament_effect_pure():
    """Holding the reliability-prior FIXED, varying temperament moves wait-time:
    a patient (low time-cost weight) agent waits strictly longer than an impatient
    one, at the SAME prior."""
    for p in (60, 80, 100):
        patient = MarshmallowWorld([2], [p]).wait_times()[0]
        impatient = MarshmallowWorld([8], [p]).wait_times()[0]
        assert patient > impatient, (p, patient, impatient)


def test_g_dissolution_prior_effect_pure():
    """Holding temperament FIXED, varying the reliability-prior moves wait-time:
    a higher prior waits strictly longer at the SAME temperament. This is the
    separation humans cannot measure."""
    for w in (2, 4, 8):
        low = MarshmallowWorld([w], [60]).wait_times()[0]
        high = MarshmallowWorld([w], [100]).wait_times()[0]
        assert high > low, (w, low, high)


def test_g_rational_impatience_kidd2013():
    """A LOW reliability-prior -> SHORTER wait EVEN for a patient temperament --
    impatience as the RATIONAL output of a correct belief, attributed to the PRIOR.
    Failable control: the SAME patient temperament with a HIGH prior waits long."""
    patient_unreliable = MarshmallowWorld([2], [60]).wait_times()[0]
    patient_reliable = MarshmallowWorld([2], [100]).wait_times()[0]
    assert patient_unreliable == 5 and patient_reliable == 25
    assert patient_reliable > patient_unreliable


def test_g_confound_wait_time_not_identifiable_for_temperament():
    """Two agents with IDENTICAL temperament but different priors show DIFFERENT
    wait-times (a naive marshmallow reading scores them as different 'self-control');
    two agents with DIFFERENT temperament but compensating priors show the SAME
    wait-time (scored identical). Both teeth of the confound."""
    # same temperament, different prior -> different wait (strictly increasing)
    same_temp = MarshmallowWorld([4, 4, 4], [60, 80, 100]).wait_times()
    assert same_temp == [3, 8, 13]
    assert same_temp[0] < same_temp[1] < same_temp[2]
    # different temperament (4x spread), compensating prior -> IDENTICAL wait
    comp = MarshmallowWorld([2, 4, 8], [60, 68, 85]).wait_times()
    assert comp == [5, 5, 5]


def test_g_glass_box_state_and_source_audit():
    """Temperament (Drive.weight), reliability-prior, elapsed, chosen_action and the
    candidate total_values are all readable from the graph; the adapter has no Python
    rule engine, no agent-decision if/else, and no reward/punishment shaping."""
    mw = MarshmallowWorld([2, 8], [60, 100])
    gb = mw.glass_box(0, t=3)
    mw.close()
    for k in ("temperament", "reliability_prior", "elapsed", "chosen_action",
              "wait_total_value", "take_total_value"):
        assert k in gb
    # temp=2, prior=60, t=3 -> wait value = 2*60 - 2*2*3 = 108 (> take 101) -> wait(1)
    assert gb["temperament"] == 2.0 and gb["reliability_prior"] == 60.0
    assert gb["wait_total_value"] == 108.0 and gb["take_total_value"] == 101.0
    assert gb["chosen_action"] == 1
    src = open(os.path.join(ROOT, "domains", "marshmallow_world.py")).read()
    for pat in ("graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("):
        assert src.count(pat) == 0, pat
    for tok in ("reward_signal", "reinforce", "backprop", "gradient"):
        assert not re.search(r"\b" + re.escape(tok) + r"\b", src), tok


def test_new_world_is_isolated_byte_identity():
    """marshmallow_delay is self_load_only: load_all_seeds must NOT load it, so the
    existing tree is byte-identical with it absent."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "marshmallow_delay" not in seeds


def test_seed_is_integer_native_and_canonical_untouched():
    seed = json.load(open(os.path.join(ROOT, "seeds", "marshmallow_delay.json")))
    assert seed.get("self_load_only") is True and seed.get("depends_on") == []
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == []
    assert [r["name"] for r in seed["rules"]] == [
        "mm_appraise_wait", "mm_appraise_take", "mm_choose"]
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == CANON_MD5

"""BLOCK 215000 -- SPITE-TO-SUCCEED gate. A grievance (an appraised slight from a
specific rival) amplifies the agent's OWN achievement via a graph RULE over the
landed 204000 core_emotions economy. This file gates the four Gs in miniature,
graph-nativity, integer-nativity, and new-world isolation (byte-identity absent).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.achieve_world import AchieveWorld   # noqa: E402


def test_g_succeed_slighted_outperforms_control_self_benefiting_and_directed():
    """A slighted, witnessed agent OUTPERFORMS an un-slighted control (higher own
    output), SELF-BENEFITING (no rival harm), and DIRECTED (no uplift when the
    rival does not witness). The Argmax RULE, not Python, chooses."""
    ctrl = AchieveWorld(slights=[], efficacy=10, observed=True)
    d_ctrl = ctrl.decide(0); ctrl.close()
    slig = AchieveWorld(slights=[(12, 0)], efficacy=10, observed=True)
    d_slig = slig.decide(0); slig.close()
    unwit = AchieveWorld(slights=[(12, 0)], efficacy=10, observed=False)
    d_unwit = unwit.decide(0); unwit.close()

    assert d_ctrl["output"] == 4                          # baseline: argmax of 8e - e^2
    assert d_slig["output"] > d_ctrl["output"]            # OUTPERFORMS
    assert d_slig["output"] == 10                         # 4 + floor(12/2)
    assert d_slig["kind_succeed"] == 1 and d_slig["rival_harm"] == 0   # self-benefiting
    assert d_unwit["output"] == 4                         # directed: unwitnessed -> no uplift


def test_g_develops_dose_response_accumulation_and_scale2_decay():
    """The grievance BUILDS from the slight (dose-response + accumulation) and
    DECAYS via the 196000 scale2 (Ashr) half-life law."""
    # dose-response: output = 4 + floor(m/2); m=0 -> baseline
    for m, exp in [(0, 4), (2, 5), (8, 8), (12, 10), (20, 14)]:
        w = AchieveWorld(slights=([(m, 0)] if m > 0 else []), efficacy=10, observed=True)
        assert w.decide(0)["output"] == exp, (m, exp)
        w.close()
    # accumulation: k slights of m=6 -> G = 6k
    for k, expG in [(1, 6), (2, 12), (3, 18)]:
        w = AchieveWorld(slights=[(6, 0)] * k, efficacy=10, observed=True)
        assert w.decide(0)["grievance"] == expG
        w.close()
    # scale2 decay: G(t) == 16 >> (t // half_life); a held grudge (H=16) persists
    for H in (1, 4, 16):
        for t in (0, H, 2 * H, 20):
            w = AchieveWorld(slights=[(16, 0)], efficacy=10, observed=True, half_life=H)
            assert w.decide(t)["grievance"] == (16 >> (t // H)), (H, t)
            w.close()
    w = AchieveWorld(slights=[(16, 0)], efficacy=10, observed=True, half_life=16)
    assert w.decide(15)["grievance"] == 16 and w.decide(16)["grievance"] == 8   # held grudge
    w.close()


def test_g_channel_efficacy_flips_succeed_to_destroy():
    """The SAME grievance channels into SUCCEED vs DESTROY gated by efficacy:
    HIGH efficacy -> amplify own achievement (self-benefiting); LOW efficacy ->
    collapse into destructive spite (harm the rival at self-cost)."""
    for eff in (5, 8, 10):
        w = AchieveWorld(slights=[(12, 0)], efficacy=eff, observed=True)
        d = w.decide(0); w.close()
        assert d["kind_succeed"] == 1 and d["output"] == 10 and d["rival_harm"] == 0, eff
    for eff in (0, 2, 4):
        w = AchieveWorld(slights=[(12, 0)], efficacy=eff, observed=True)
        d = w.decide(0); w.close()
        assert d["kind_succeed"] == 0 and d["output"] == 0 and d["rival_harm"] == 6, eff


def test_new_world_is_isolated_byte_identity():
    """grievance_succeed is self_load_only: load_all_seeds must NOT load it, so the
    existing tree is byte-identical with it absent."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "grievance_succeed" not in seeds


def test_seed_is_integer_native_and_canonical_untouched():
    import hashlib
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "grievance_succeed.json")))
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
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == "793ce09ed498a749abb79aeaea44b92e"

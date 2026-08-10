#!/usr/bin/env python3
"""bigville R20 (block 268000) glass-box run -- COUNCIL MEETINGS & the NOTICEBOARD.
Drives the isolated governance substrate through the four gate scenarios and writes
the measured read-offs to results/bigville_council/summary.json.

Every number here is a graph read-off; every DECISION is a seed rule (see
BIGVILLE_COUNCIL_PREREG.md). The public/private correlation is a MEASUREMENT
(Pearson r over per-meeting (public_demand, held_decision) read-offs) -- not a new
primitive. The adapter only ingests graph data + reads state.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_council_world import BigvilleCouncilWorld     # noqa: E402

DEMANDS = [10, 15, 20, 25, 30, 35]


def _pearson(xs, ys):
    """Pearson r over the (demand, decision) read-offs. Zero covariance (a captured
    council whose decision never moves) -> r defined as 0.0 (theatre)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / (sxx ** 0.5 * syy ** 0.5)


def _council(captured):
    # base_position == the mayor's benevolent stated_position (10) so ablating
    # malice collapses the held decision onto the public address (234 gap -> 0).
    w = BigvilleCouncilWorld()
    w.add_council(captured=captured)
    w.add_mayor("mayor", stated_position=10)
    # a 3-member backing-graph (the collective decision_value)
    for nm in ("a", "b", "c"):
        w.add_member(nm, base_position=10, self_serving_premium=50,
                     is_clerk=(nm == "a"), clerk_bias=0.0)
    return w


def gate_two_tier():
    """Public address perceived; private decision occluded; off-cadence no meeting;
    ablate private tier -> the town perceives the decision too."""
    w = _council(captured=0)
    w.add_resident("t", literate=1, at_hall=1)
    on = w.convene(now_day=6, cadence=3, public_demand=25, private_on=1, malice_on=0)
    town_on = dict(heard_address=w.heard_address_of("t"),
                   knows_address=w.knows_address_of("t"),
                   heard_decision=w.heard_decision_of("t"))
    w.close()
    w2 = _council(captured=0)
    w2.add_resident("t", literate=1, at_hall=1)
    off = w2.convene(now_day=6, cadence=3, public_demand=25, private_on=0, malice_on=0)
    town_off = dict(heard_address=w2.heard_address_of("t"),
                    heard_decision=w2.heard_decision_of("t"),
                    knows_decision=w2.knows_decision_of("t"))
    w2.close()
    w3 = _council(captured=0)
    off_cadence = w3.convene(now_day=7, cadence=3, public_demand=25)
    w3.close()
    return dict(private_on=dict(meeting=on, town=town_on),
                private_ablated=dict(meeting=off, town=town_off),
                off_cadence=off_cadence,
                verdict="town hears the ADDRESS not the DECISION while private_on; "
                        "ablate the private tier -> town hears the decision; "
                        "off-cadence -> no meeting")


def gate_influence_or_theatre():
    """HEADLINE (agency vs structure, MEASURED): Pearson r between public demand and
    the private decision. Responsive council -> ~+1 (agency); captured -> ~0
    (theatre over a pre-made decision)."""
    resp_dec, capt_dec = [], []
    for D in DEMANDS:
        wr = _council(captured=0)
        resp_dec.append(wr.convene(now_day=0, cadence=1, public_demand=D,
                                   malice_on=0)["held_decision"])
        wr.close()
        wc = _council(captured=1)
        capt_dec.append(wc.convene(now_day=0, cadence=1, public_demand=D,
                                   malice_on=1)["held_decision"])
        wc.close()
    return dict(demands=DEMANDS,
                responsive=dict(decisions=resp_dec, r=_pearson(DEMANDS, resp_dec)),
                captured=dict(decisions=capt_dec, r=_pearson(DEMANDS, capt_dec)),
                verdict="responsive r~+1 (public voice reaches the lever = AGENCY); "
                        "captured r~0 (ritual over a pre-made decision = STRUCTURE)")


def gate_institutional_gap():
    """234 at institutional scale: benevolent address over self-serving decision.
    Ablate malice -> the gap closes."""
    out = {}
    for malice in (1, 0):
        w = _council(captured=1)
        r = w.convene(now_day=0, cadence=1, public_demand=15, malice_on=malice)
        out["malice_on" if malice else "malice_off"] = dict(
            public_address=r["public_address"], held_decision=r["held_decision"],
            stated_held_gap=r["stated_held_gap"])
        w.close()
    return dict(**out,
                verdict="malice_on: address(10) << decision(60), gap>0; "
                        "malice_off: address==decision, gap 0 (the gap closes)")


def gate_noticeboard():
    """Clerk writes (biased) + posts; a resident learns the law only via R1 access +
    R18 literacy. Illiterate/distant -> officially known yet personally unknown.
    Ablate literacy gate -> uniform knowledge."""
    def run(gate):
        w = BigvilleCouncilWorld()
        w.add_council(captured=1)
        w.add_mayor("mayor", stated_position=10)
        w.add_member("clerk", base_position=40, self_serving_premium=20,
                     is_clerk=1, clerk_bias=7)     # a BIASED clerk distorts the minutes
        w.add_member("b", base_position=40, self_serving_premium=20)
        w.add_resident("lit_near", literate=1, at_hall=1)
        w.add_resident("ill_near", literate=0, at_hall=1)
        w.add_resident("lit_far", literate=1, at_hall=0)
        w.convene(now_day=0, cadence=1, public_demand=15, malice_on=1)
        notice = w.post_notice(literacy_gate_on=gate)
        rows = {n: dict(knows_law_flag=w.knows_law_flag_of(n),
                        knows_law=w.knows_law_of(n))
                for n in ("lit_near", "ill_near", "lit_far")}
        dec = w.held_decision()
        w.close()
        return notice, rows, dec

    notice, rows, dec = run(gate=1)
    _, rows_ablated, _ = run(gate=0)
    return dict(held_decision=dec, notice=notice,
                clerk_distortion=notice["recorded"] - dec,
                literacy_gate_on=rows, literacy_gate_ablated=rows_ablated,
                verdict="biased clerk: recorded != decision (institutional 234); "
                        "only the literate-at-hall resident learns the law; "
                        "illiterate/distant officially_known yet personally UNKNOWN; "
                        "ablate literacy gate -> uniform knowledge")


def main():
    summary = dict(
        rung="R20", block=268000,
        title="council meetings & the noticeboard -- two-tier governance + the public written record",
        base_sha="350a45c4078403510bd1c83ea389a06ae6dadacd",
        gates=dict(
            G_two_tier_meeting=gate_two_tier(),
            G_public_influence_or_theatre=gate_influence_or_theatre(),
            G_institutional_stated_ne_held=gate_institutional_gap(),
            G_noticeboard_promulgates=gate_noticeboard(),
        ),
        no_new_rust=True, seeds_self_load_only=True,
    )
    out_dir = os.path.join(_ROOT, "results", "bigville_council")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print("wrote", path)
    g = summary["gates"]["G_public_influence_or_theatre"]
    print("responsive r=%.4f  captured r=%.4f" % (g["responsive"]["r"], g["captured"]["r"]))


if __name__ == "__main__":
    main()

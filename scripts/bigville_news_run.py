#!/usr/bin/env python3
"""bigville R21 (block 269000) glass-box run -- THE NEWSPAPER & THE REPORTER.
Drives the isolated press substrate through the four gate scenarios and writes the
measured read-offs to results/bigville_news/summary.json.

Every number here is a graph read-off; every DECISION is a seed rule (see
BIGVILLE_NEWS_PREREG.md). The two-channel error and the coalition informed-count
are MEASUREMENTS -- not new primitives. The adapter only ingests graph data + reads
state.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_news_world import BigvilleNewsWorld          # noqa: E402


def _world(*, captured=0, active=1, damaging=0, truth=60, reporter_bias=0,
           clerk_bias=None, reporter_witnessed=1):
    w = BigvilleNewsWorld()
    w.add_town()
    w.add_event(truth_value=truth, damaging_to_owner=damaging)
    w.add_reporter("rep", witnessed=reporter_witnessed)
    w.add_paper("gazette", captured=captured, active=active)
    w.add_story(reporter_bias=reporter_bias)
    if clerk_bias is not None:
        w.add_minutes(clerk_bias=clerk_bias)
    return w


def gate_propagates_beliefs():
    """A literate non-witness learns a distant event FROM the paper (beyond earshot);
    an illiterate non-witness stays ignorant (R18 divide); an illiterate witness
    knows directly; ablate the paper -> the literate non-witness stays ignorant."""
    def readers(active):
        w = _world(truth=60, reporter_bias=10, active=active)
        w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
        w.add_resident("ill_far", literate=0, witnessed=0, reads=1)
        w.add_resident("ill_wit", literate=0, witnessed=1, reads=1)
        w.publish()
        rows = {n: dict(flag=w.knows_event_flag_of(n), belief=w.knows_event_of(n))
                for n in ("lit_far", "ill_far", "ill_wit")}
        printed = w.printed()
        w.close()
        return dict(printed=printed, residents=rows)

    return dict(paper_present=readers(active=1), paper_ablated=readers(active=0),
                truth=60.0,
                verdict="literate non-witness learns FROM the paper (belief 70, the "
                        "biased rendering); illiterate non-witness ignorant (R18 "
                        "divide); illiterate WITNESS knows the true 60 directly; "
                        "ablate the paper -> the literate non-witness ignorant too")


def gate_free_vs_captured_press():
    """Independent paper prints John's corruption; captured paper launders/omits it;
    ablate the capture -> it prints; a captured paper still prints an ordinary
    story."""
    def run(captured, damaging):
        w = _world(captured=captured, damaging=damaging, reporter_bias=10)
        w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
        w.publish()
        out = dict(written=w.written(), suppressed=w.suppressed(), printed=w.printed(),
                   reader_flag=w.knows_event_flag_of("lit_far"))
        w.close()
        return out

    return dict(independent_damaging=run(captured=0, damaging=1),
                captured_damaging=run(captured=1, damaging=1),
                captured_nondamaging=run(captured=1, damaging=0),
                verdict="independent paper prints the corruption (readers learn); "
                        "captured paper suppresses it (readers ignorant); ablate "
                        "capture -> prints; capture is TARGETED (still prints an "
                        "ordinary story)")


def gate_second_reconstruction_channel():
    """The paper and the noticeboard are TWO lossy renderings of ONE event; WE hold
    the ground truth -> both scoreable, DIFFERENT bias profiles."""
    w = _world(truth=60, reporter_bias=15, clerk_bias=-25)
    w.add_resident("reader", literate=1, witnessed=0, reads=1)
    w.add_resident("witness", literate=1, witnessed=1, reads=1)
    w.publish()
    truth, paper, minutes = w.truth_value(), w.content(), w.minutes_value()
    out = dict(truth=truth, paper_rendering=paper, noticeboard_rendering=minutes,
               error_paper=abs(paper - truth), error_noticeboard=abs(minutes - truth),
               reader_belief=w.knows_event_of("reader"),
               witness_belief=w.knows_event_of("witness"))
    w.close()
    return dict(**out,
                verdict="truth 60; paper 75 (reporter ATTACKS: +15); noticeboard 35 "
                        "(clerk PROTECTS: -25) -- three distinct renderings, DIFFERENT "
                        "bias profiles, both scoreable. Reader holds the paper's biased "
                        "75; the witness holds the true 60")


def gate_feeds_collective_action():
    """A shared grievance become common knowledge via the paper -> the coalition
    forms; capture the paper -> no coordination; the count binds (quorum)."""
    def run(captured, quorum, nreaders):
        w = _world(captured=captured, damaging=1, reporter_bias=10)
        w.add_coalition(quorum=quorum)
        for i in range(nreaders):
            w.add_resident("r%d" % i, literate=1, witnessed=0, reads=1)
        w.publish()
        out = dict(printed=w.printed(), suppressed=w.suppressed(),
                   informed=w.informed(), quorum=quorum, formed=w.formed())
        w.close()
        return out

    return dict(independent=run(captured=0, quorum=2, nreaders=3),
                captured=run(captured=1, quorum=2, nreaders=3),
                below_quorum=run(captured=0, quorum=2, nreaders=1),
                verdict="independent paper -> 3 informed >= quorum 2 -> coalition forms; "
                        "captured -> 0 informed -> no coalition (coordination suppressed); "
                        "below quorum (1 informed) -> no coalition (the COUNT binds)")


def main():
    summary = dict(
        rung="R21", block=269000,
        title="the newspaper & the reporter -- the fourth estate, a second reconstruction channel",
        base_sha="59653fd443fb0e0894b5ea59a51bb39402260f4e",
        gates=dict(
            G_paper_propagates_beliefs=gate_propagates_beliefs(),
            G_free_vs_captured_press=gate_free_vs_captured_press(),
            G_second_reconstruction_channel=gate_second_reconstruction_channel(),
            G_paper_feeds_collective_action=gate_feeds_collective_action(),
        ),
        no_new_rust=True, seeds_self_load_only=True,
    )
    out_dir = os.path.join(_ROOT, "results", "bigville_news")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print("wrote", path)
    s = summary["gates"]["G_second_reconstruction_channel"]
    print("two channels: truth=%.0f paper=%.0f noticeboard=%.0f (err %.0f / %.0f)" % (
        s["truth"], s["paper_rendering"], s["noticeboard_rendering"],
        s["error_paper"], s["error_noticeboard"]))
    c = summary["gates"]["G_free_vs_captured_press"]
    print("press: independent printed=%d  captured printed=%d" % (
        c["independent_damaging"]["printed"], c["captured_damaging"]["printed"]))


if __name__ == "__main__":
    main()

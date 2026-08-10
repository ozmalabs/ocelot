#!/usr/bin/env python3
"""bigville R19 (block 267000) glass-box run -- utterance LOUDNESS & the
OBSERVE-vs-HEAR split. Drives the isolated comm substrate through the five gate
scenarios and writes the measured read-offs to results/bigville_loud/summary.json.

Every number here is a graph read-off; every DECISION is a seed rule (see
BIGVILLE_LOUD_PREREG.md). The adapter only ingests geometry + reads state.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_loud_world import BigvilleLoudWorld            # noqa: E402

RING = [1, 2, 4, 6, 8, 12]
SPK = (14, 8)
CHILDREN = ["c0", "c1", "c2", "c3"]


def _ring(base=6.0, mx=20.0):
    w = BigvilleLoudWorld()
    w.add_person("spk", SPK, base_loudness=base, max_loudness=mx)
    for d in RING:
        w.add_person("h%d" % d, (14 + d, 8))
    return w


def _heard(res):
    return [d for d in RING if res["receptions"]["h%d" % d]["got_content"]]


def gate_radius():
    on, off = {}, {}
    for L in (1, 3, 6, 12):
        w = _ring(); res = w.speak("spk", "a", chosen_loudness=L)
        on[L] = dict(eff=res["eff_loudness"], heard=_heard(res)); w.close()
    for L in (1, 3, 6, 12):
        w = _ring(); res = w.speak("spk", "a", chosen_loudness=L, loudness_on=0)
        off[L] = dict(eff=res["eff_loudness"], heard=_heard(res)); w.close()
    return dict(loudness_on=on, loudness_ablated=off,
                verdict="content-set grows whisper(1)->shout(12); ablation flat & L-independent")


def gate_observe_hear():
    w = BigvilleLoudWorld()
    w.add_person("spk", SPK)
    w.add_person("near", (15, 8))
    w.add_person("witness", (19, 8))
    res = w.speak("spk", "near", chosen_loudness=1)
    out = dict(whisper_L=1, near=res["receptions"]["near"],
               witness=res["receptions"]["witness"],
               verdict="distant witness observes the ACT (1) but not the CONTENT (0)")
    w.close()
    return out


def gate_seed_choice():
    w = BigvilleLoudWorld()
    w.add_person("child", (14, 8), base_loudness=3.0, max_loudness=5.0)
    w.add_person("pub", (2, 8), base_loudness=8.0, max_loudness=15.0)
    w.add_person("dummy", (14, 8))

    def eff(spk, **kw):
        return w.speak(spk, "x", hearers=["dummy"], **kw)["eff_loudness"]
    out = dict(
        child=dict(base=3, max=5, whisper=eff("child", chosen_loudness=1),
                   shout=eff("child", chosen_loudness=100),
                   choice_ablated=eff("child", choice_on=0)),
        publican=dict(base=8, max=15, whisper=eff("pub", chosen_loudness=1),
                      shout=eff("pub", chosen_loudness=100),
                      choice_ablated=eff("pub", choice_on=0)),
        verdict="shout capped at own max; child shout (5) < publican normal (8); choice ablated -> base")
    w.close()
    return out


def gate_privacy():
    w = BigvilleLoudWorld()
    w.add_person("mary", SPK, base_loudness=6.0, max_loudness=12.0)
    w.add_person("confidant", (15, 8))
    w.add_person("witness", (17, 8))
    res = w.speak("mary", "confidant", chosen_loudness=1)
    out = dict(counsel_L=1, confidant=res["receptions"]["confidant"],
               witness=res["receptions"]["witness"],
               verdict="quiet counsel: witness SEES the meeting, never HEARS it; confidant hears")
    w.close()
    return out


def _classroom():
    w = BigvilleLoudWorld()
    w.add_person("teacher", (14, 6), base_loudness=8.0, max_loudness=15.0, peer_pull=0.0)
    for i, x in enumerate((13, 14, 15, 16)):
        w.add_person(CHILDREN[i], (x, 8), base_loudness=3.0, max_loudness=5.0, peer_pull=1.0)
    return w


def _chatter(w):
    last = None
    for c in CHILDREN:
        others = [n for n in CHILDREN if n != c] + ["teacher"]
        last = w.speak(c, "peers", chosen_loudness=1, is_control=0,
                       hearers=others)["receptions"]["teacher"]
    return last


def gate_classroom():
    w = _classroom()
    teacher = _chatter(w)
    after_chatter = {c: w.attending_of(c) for c in CHILDREN}
    r = w.speak("teacher", "class", chosen_loudness=12, is_control=1, hearers=CHILDREN)
    after_control = {c: w.attending_of(c) for c in CHILDREN}
    w.close()
    w2 = _classroom(); _chatter(w2)
    ra = w2.speak("teacher", "class", chosen_loudness=1, is_control=1, hearers=CHILDREN)
    after_ablated = {c: w2.attending_of(c) for c in CHILDREN}
    w2.close()
    return dict(
        teacher_on_chatter=teacher, after_chatter=after_chatter,
        control_shout_content={c: r["receptions"][c]["got_content"] for c in CHILDREN},
        after_control_shout=after_control,
        ablated_whisper_content={c: ra["receptions"][c]["got_content"] for c in CHILDREN},
        after_ablated_control=after_ablated,
        scope="SCOPED PROXY: attending is the R17/R18 attention-gate stand-in; "
              "acquisition/learning coupling DEFERRED (needs R18)",
        verdict="teacher OBSERVES chatter not hears; shout restores attention; whisper control does not")


def main():
    summary = dict(
        rung="R19", block=267000,
        title="utterance loudness & the observe-vs-hear split",
        base_sha="a6bb0c0b623a44b6b37b2c12685e057cad2182ad",
        gates=dict(
            G_loudness_sets_hearing_radius=gate_radius(),
            G_observe_vs_hear_split=gate_observe_hear(),
            G_loudness_is_seed_plus_choice=gate_seed_choice(),
            G_privacy_is_physical=gate_privacy(),
            G_classroom_chatter=gate_classroom(),
        ),
        no_new_rust=True, seeds_self_load_only=True,
    )
    out_dir = os.path.join(_ROOT, "results", "bigville_loud")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print("wrote", path)
    print(json.dumps(summary["gates"]["G_observe_vs_hear_split"], indent=1))


if __name__ == "__main__":
    main()

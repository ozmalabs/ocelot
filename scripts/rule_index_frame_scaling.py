"""rule_index_frame_scaling — the DECISIVE measurement: does the coercion
first-fire scan grow with the number of FRAMES/nodes in the graph (holding the
event count fixed at 1)? This is the concern's real claim ("matches over the
large frame set per event"). We inject N *junk* SelectionalFrame nodes (no
satisfied_by, no frames_theme edge) and time the SAME single-event first fire.

If cost is FLAT in junk-frame count -> the engine's edges_by_type index already
bounds the scan (foveation already present at the driver). If it GROWS linearly
-> there is a real unindexed scan to fix.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_index_frame_scaling.py
"""
from __future__ import annotations
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from substrate_rs import ext
from domains import dictionary_lexicon as dl
from domains import cognitive_disambiguation as cd


class _Agent:
    def __init__(self, s, node):
        self.s = s; self.inner = s._inner; self.agent = node


def _fresh():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    cd.ensure_metonymy_codebook(ag)
    return ag


def _person(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "person",
                                   "coref_animate": 1.0, "coref_mentions": 2.0})


def _event(s, verb, surface, role, arg):
    ev = s.add_node("SmEvent", {"verb": verb, "surface": surface})
    s._inner.add_edge_unchecked(ev, role, arg)
    return ev


def _coerce_theme_us(ag):
    for name, micros, count, prog in ag.s._inner.rule_costs():
        if name == "coerce_theme":
            return micros, count, prog
    return (0, 0, 0)


def measure(n_junk_frames: int, reps: int = 5):
    best = None; det = None
    for _ in range(reps):
        ag = _fresh()
        s = ag.s
        # inject junk frames (no edges) — pure inventory growth
        for i in range(n_junk_frames):
            s.add_node("SelectionalFrame", {"verb_synset": f"junk_{i}.v.99",
                                            "role": "theme", "accepts": ["nothing"]})
        _event(s, "read", "read", "theme", _person(s, "shakespeare"))
        cd._prep_frames(ag); cd._prep_acquire(ag); cd._mark_subject(ag, None)
        s._inner.reset_rule_costs()
        t0 = time.perf_counter()
        steps = ext.run_rules(s)
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt; det = (steps, _coerce_theme_us(ag),
                              len(s.nodes("SelectionalFrame")))
    return best, det


def main():
    print("=" * 84)
    print("DECISIVE: coercion first-fire vs FRAME COUNT (1 event fixed)")
    print("=" * 84)
    print(f"{'junk frames':>11} | {'total frames':>12} | {'first-fire ms':>13} | {'coerce_theme us/cnt/prog':>26}")
    print("-" * 84)
    for n in (0, 100, 500, 1000, 2000, 4000, 8000):
        best, (steps, ct, tf) = measure(n)
        print(f"{n:>11} | {tf:>12} | {best*1e3:>13.3f} | {ct[0]:>6}/{ct[1]}/{ct[2]}")
    print()
    print("FLAT in frame count => engine already bounds the scan (index present).")
    print("LINEAR in frame count => a real unindexed scan the concern names.")


if __name__ == "__main__":
    main()

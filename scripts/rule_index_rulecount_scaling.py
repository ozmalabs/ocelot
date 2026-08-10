"""rule_index_rulecount_scaling — the OTHER half of the concern:
"run_rules enumerates the whole rule set per fire". Inject N inert rules
(anchored on a node TYPE that has zero instances) and time the SAME coercion
first-fire. If run_rules cost grows with total rule count -> the per-pass
to_try scan is the bottleneck as rules grow (the self-mod session grows them),
and type-indexed skipping (only try rules whose anchor-type has dirty nodes)
would bound it.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_index_rulecount_scaling.py
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


def _inert_rule(i, match_type=None):
    r = {"name": f"inert_{i}",
         "match": [["z", f"zz_never_{i}", "w"]],   # edge type that never exists
         "effects": [["set_attr", "z", "touched", 1.0]]}
    if match_type:
        r["match_type"] = match_type
    return r


def measure(n_inert: int, match_type=None, reps: int = 5):
    best = None; det = None
    for _ in range(reps):
        ag = _fresh(); s = ag.s
        for i in range(n_inert):
            s._inner.add_rule(_inert_rule(i, match_type))
        _event(s, "read", "read", "theme", _person(s, "shakespeare"))
        cd._prep_frames(ag); cd._prep_acquire(ag); cd._mark_subject(ag, None)
        t0 = time.perf_counter()
        steps = ext.run_rules(s)
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt; det = (steps, ext.rule_count(s))
    return best, det


def main():
    print("=" * 78)
    print("run_rules first-fire vs TOTAL RULE COUNT (1 coercion event fixed)")
    print("=" * 78)
    print(f"{'inert rules':>11} | {'rule_count':>10} | {'first-fire ms (no mtype)':>24} | {'w/ match_type NoSuchType':>24}")
    print("-" * 78)
    for n in (0, 50, 100, 250, 500, 1000):
        b0, (s0, rc0) = measure(n, match_type=None)
        b1, (s1, rc1) = measure(n, match_type="NoSuchType")
        print(f"{n:>11} | {rc0:>10} | {b0*1e3:>24.3f} | {b1*1e3:>24.3f}")
    print()
    print("If 'no mtype' GROWS with rule count but 'w/ match_type' stays FLAT,")
    print("type-indexed skipping bounds the to_try scan as rules grow.")


if __name__ == "__main__":
    main()

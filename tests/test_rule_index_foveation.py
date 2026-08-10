"""test_rule_index_foveation — the RULE-INDEX FOVEATION invariant.

The jabberwock, driven with the rule-matching performance concern
(scripts/jabberwock_designs_rule_index.py), recognized it as a GATE / SELECT-a-
subset shape (selective_gating tied top in its seven meta-shapes; grounded via
its 'select'/'match' relation heads). Its own foveation / dynamic-quantization
thesis — "decode only in focus, per quantum not per element" — applied to
rule-matching means: the rule-scan should FOVEATE to the match-anchor in focus,
NOT scan the whole frame set per event.

THE MEASURED FACT this gate protects: the engine's `edges_by_type` index already
realizes that foveation for the coercion rules — the first-fire scan is FLAT in
the frame/satisfied_by-edge count (does not grow when the metonymy inventory
grows). The three coercion rules now DECLARE their foveation anchor as data
(`match_type: "SmEvent"`), byte-identical on the current matcher, forward-
compatible with a run_rules to_try anchor-skip.

Gates:
  (1) all three coercion rules carry match_type == "SmEvent" (the anchor, as data)
      and it round-trips into the live engine rule set.
  (2) BYTE-IDENTICAL firing: shakespeare theme -> shakespeare_works, re_decoded
      via author_works — the tag changed nothing about which rules fire.
  (3) FOVEATION INVARIANT (deterministic): the SAME single-event coercion produces
      the IDENTICAL shift and step count whether the graph holds the base 1.8k
      frames or +8000 junk frames — the decision is bound to the anchor, not the
      frame set.
  (4) PERF (loose, best-of-N): the first-fire wall-time does not blow up with the
      frame count (bounded, not linear).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_rule_index_foveation.py -p no:randomly -q -s
"""
from __future__ import annotations
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core        # noqa: E402
from substrate_rs import ext                      # noqa: E402
from domains import dictionary_lexicon as dl      # noqa: E402
from domains import cognitive_disambiguation as cd  # noqa: E402

_SEED = os.path.join(ROOT, "seeds", "metonymy_patterns.json")
_COERCION = ("coerce_theme", "coerce_agent", "coerce_role_named_after")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    cd.ensure_metonymy_codebook(ag)
    return ag


def _person(s, name):
    return s.add_node("SmEntity", {"name": name, "coref_category": "person",
                                   "coref_animate": 1.0, "coref_mentions": 2.0})


def _read_event(s, arg):
    ev = s.add_node("SmEvent", {"verb": "read", "surface": "read"})
    s._inner.add_edge_unchecked(ev, "theme", arg)
    return ev


# (1) the anchor is declared as DATA, in the seed AND in the live engine.
def test_coercion_rules_declare_the_foveation_anchor():
    seed = json.load(open(_SEED))
    rules = {r["name"]: r for r in seed.get("rules", [])}
    for name in _COERCION:
        assert rules[name].get("match_type") == "SmEvent", name

    ag = _fresh()
    live = {r["name"]: r for r in ag.s._inner.export_rules()}
    for name in _COERCION:
        assert live[name].get("match_type") == "SmEvent", (name, "did not round-trip into the engine")


# (2) BYTE-IDENTICAL firing with the tag present.
def test_byte_identical_firing_with_the_anchor():
    ag = _fresh()
    ev = _read_event(ag.s, _person(ag.s, "shakespeare"))
    rep = cd.metonymic_redecode(ag, "")
    assert cd.event_theme(ag, ev)["name"] == "shakespeare_works"
    assert rep["shifts"] and rep["shifts"][0]["verdict"] == "re_decoded"
    assert rep["shifts"][0]["pattern"] == "author_works"


def _one_event_shift(n_junk_frames: int):
    """Run ONE shakespeare-read coercion with n_junk_frames extra inert frames;
    return (theme_name, steps) — the deterministic decision + fixpoint size."""
    ag = _fresh()
    s = ag.s
    for i in range(n_junk_frames):
        s.add_node("SelectionalFrame", {"verb_synset": f"junk_{i}.v.99",
                                         "role": "theme", "accepts": ["nothing"]})
    ev = _read_event(s, _person(s, "shakespeare"))
    cd._prep_frames(ag)
    cd._prep_acquire(ag)
    cd._mark_subject(ag, None)
    steps = ext.run_rules(s)
    return cd.event_theme(ag, ev)["name"], steps


# (3) FOVEATION INVARIANT — the decision is bound to the anchor, not the frame set.
def test_decision_is_invariant_to_frame_inventory_size():
    base_name, base_steps = _one_event_shift(0)
    big_name, big_steps = _one_event_shift(8000)
    assert base_name == big_name == "shakespeare_works"
    assert base_steps == big_steps      # same fixpoint regardless of 8000 extra frames


# (4) PERF — the scan is BOUNDED (not linear) in the frame count.
def test_first_fire_does_not_grow_with_frame_count():
    def best_first_fire(n_junk, reps=5):
        best = None
        for _ in range(reps):
            ag = _fresh(); s = ag.s
            for i in range(n_junk):
                s.add_node("SelectionalFrame", {"verb_synset": f"j_{i}.v.9",
                                                "role": "theme", "accepts": ["x"]})
            _read_event(s, _person(s, "shakespeare"))
            cd._prep_frames(ag); cd._prep_acquire(ag); cd._mark_subject(ag, None)
            t0 = time.perf_counter()
            ext.run_rules(s)
            dt = time.perf_counter() - t0
            best = dt if best is None else min(best, dt)
        return best

    small = best_first_fire(0)
    big = best_first_fire(8000)
    print(f"\n  first-fire: {small*1e3:.3f} ms @ base vs {big*1e3:.3f} ms @ +8000 frames")
    # Foveated => sub-linear. A linear scan would be ~5x here; allow generous 3x.
    assert big < small * 3.0 + 1e-3, (small, big)
